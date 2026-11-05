"""Hybrid recommender for NextWatch.

Four signals, each scores every film for one user:
  pop      popularity (how many users liked the film)
  content  TF-IDF vectors of genres, title and description; cosine similarity to the user's taste profile
  knn      item-based nearest neighbours: films that the same people liked (cosine on the user x film matrix)
  als      implicit-feedback matrix factorisation (Alternating Least Squares), new users handled by fold-in

Each signal is rank-normalised and the four are blended with weights tuned on a validation set.
A user is described by `history`: {movie_id: strength}, strength > 0 liked (bigger = stronger), < 0 disliked.
"""
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import rankdata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

COMPONENTS = ["pop", "content", "knn", "als"]


def movie_text(row):
    """Text used for the TF-IDF vector. Genres are repeated so they weigh more than description words."""
    genres = [g.strip().lower().replace("-", "").replace(" ", "") for g in str(row.get("genres") or "").split(",") if g.strip()]
    tokens = " ".join(f"g_{g}" for g in genres)
    return f"{(tokens + ' ') * 3}{row.get('title') or ''} {str(row.get('overview') or '')[:400]}"


def platform_strength(df):
    """Turn NextWatch interactions (watch %, rating, like) into signed strengths. Ambiguous rows are dropped."""
    from features import make_label

    labels = df.apply(make_label, axis=1)
    bonus = ((df["rating"] >= 8).astype(float) + (df["reaction"] == 1).astype(float)
             + (df["completion_ratio"] >= 0.9).astype(float)) * 0.5
    strength = pd.Series(np.nan, index=df.index)
    strength[labels == 1] = 1 + bonus[labels == 1]
    strength[labels == 0] = -1.0
    return df.assign(strength=strength).dropna(subset=["strength"])


def _solve(fixed, fixed_t_fixed, idx, cm1, cp, reg):
    """One ALS least-squares step for a single user (or item) given the other side's factors."""
    f = fixed[idx]
    a = fixed_t_fixed + (f.T * cm1) @ f + reg * np.eye(fixed.shape[1])
    return np.linalg.solve(a, f.T @ cp)


class HybridRecommender:
    def __init__(self, factors=24, reg=0.1, alpha=20.0, iters=12, knn_k=30, neg_conf=0.5, seed=7):
        self.factors, self.reg, self.alpha, self.iters = factors, reg, alpha, iters
        self.knn_k, self.neg_conf, self.seed = knn_k, neg_conf, seed
        self.weights = dict(zip(COMPONENTS, [0.1, 0.5, 0.2, 0.2]))  # untuned default, replaced by tune()

    # ------------------------------------------------------------------ training
    def fit(self, inter, movies):
        """inter: user_id, movie_id, strength.  movies: movie_id, genres, title, overview (title/overview optional)."""
        self.movie_ids = movies["movie_id"].to_numpy()
        self.idx = {int(m): i for i, m in enumerate(self.movie_ids)}
        n = len(self.movie_ids)

        texts = [movie_text(r) for _, r in movies.iterrows()]
        self.vec = TfidfVectorizer(stop_words="english", sublinear_tf=True, ngram_range=(1, 2))
        self.T = self.vec.fit_transform(texts).tocsr()          # item feature vectors (L2-normalised)

        inter = inter[inter["movie_id"].isin(self.idx)]
        users = {u: i for i, u in enumerate(inter["user_id"].unique())}
        u_ix = inter["user_id"].map(users).to_numpy()
        i_ix = inter["movie_id"].map(self.idx).to_numpy()
        s = inter["strength"].to_numpy(dtype=float)
        pos = s > 0

        self.pop = np.log1p(np.bincount(i_ix[pos], minlength=n)).astype(float)

        # item-KNN: cosine similarity between films, keep each film's top-k neighbours
        r = sparse.csr_matrix((s[pos], (u_ix[pos], i_ix[pos])), shape=(len(users), n))
        sim = cosine_similarity(r.T, dense_output=True)
        np.fill_diagonal(sim, 0.0)
        for row in sim:
            if n > self.knn_k:
                row[np.argpartition(row, -self.knn_k)[:-self.knn_k]] = 0.0
        self.sim = sparse.csr_matrix(sim)

        # implicit ALS: preference p = 1 for liked, 0 for disliked; confidence grows with strength
        cm1 = np.where(pos, self.alpha * np.abs(s), self.alpha * self.neg_conf)   # confidence - 1
        cp = np.where(pos, 1 + self.alpha * np.abs(s), 0.0)                        # confidence * preference
        by_user = [np.where(u_ix == u)[0] for u in range(len(users))]
        by_item = [np.where(i_ix == i)[0] for i in range(n)]
        rng = np.random.default_rng(self.seed)
        x = rng.normal(0, 0.01, (len(users), self.factors))
        y = rng.normal(0, 0.01, (n, self.factors))
        for _ in range(self.iters):
            yty = y.T @ y
            for u, rows in enumerate(by_user):
                x[u] = _solve(y, yty, i_ix[rows], cm1[rows], cp[rows], self.reg) if len(rows) else 0
            xtx = x.T @ x
            for i, rows in enumerate(by_item):
                y[i] = _solve(x, xtx, u_ix[rows], cm1[rows], cp[rows], self.reg) if len(rows) else 0
        self.Y, self.YtY = y, y.T @ y
        return self

    # ------------------------------------------------------------------ scoring
    def components(self, history):
        """Raw score of every film for one user, one column per signal (rows follow self.movie_ids)."""
        n = len(self.movie_ids)
        items = [(self.idx[m], s) for m, s in history.items() if m in self.idx]
        out = np.zeros((n, len(COMPONENTS)))
        out[:, 0] = self.pop
        if not any(s > 0 for _, s in items):
            return out                                   # nothing liked yet: only popularity has a signal
        h = np.array([i for i, _ in items])
        s = np.array([v for _, v in items], dtype=float)
        w = np.where(s > 0, s, 0.5 * s)                  # dislikes count half as much, with a negative sign

        profile = sparse.csr_matrix(w) @ self.T[h]       # user taste vector in TF-IDF space
        out[:, 1] = (self.T @ profile.T).toarray().ravel()

        v = np.zeros(n)
        v[h] = w
        out[:, 2] = self.sim.T @ v                       # item-KNN

        pos = s > 0
        cm1 = np.where(pos, self.alpha * np.abs(s), self.alpha * self.neg_conf)
        cp = np.where(pos, 1 + self.alpha * np.abs(s), 0.0)
        out[:, 3] = self.Y @ _solve(self.Y, self.YtY, h, cm1, cp, self.reg)   # ALS fold-in
        return out

    @staticmethod
    def normalise(comp, seen_mask):
        """Rank-normalise each signal among the films the user has not seen yet (0 = worst, 1 = best)."""
        out = np.zeros_like(comp)
        keep = ~seen_mask
        for j in range(comp.shape[1]):
            col = comp[keep, j]
            if len(col) and np.ptp(col) > 0:
                out[keep, j] = rankdata(col) / len(col)
        return out

    def recommend(self, history, k=10, exclude=()):
        """Top-k (movie_id, score) for one user, best first."""
        seen = np.zeros(len(self.movie_ids), dtype=bool)
        for m in list(history) + list(exclude):
            if m in self.idx:
                seen[self.idx[m]] = True
        norm = self.normalise(self.components(history), seen)
        score = norm @ np.array([self.weights[c] for c in COMPONENTS])
        score[seen] = -np.inf
        order = np.argsort(-score)[:k]
        return [(int(self.movie_ids[i]), float(score[i])) for i in order if np.isfinite(score[i])]

    # ------------------------------------------------------------------ evaluation
    def prepare_cases(self, histories, targets):
        """Pre-compute normalised signals for every user so weights can be compared quickly."""
        cases = []
        for u, target in targets.items():
            hist = histories.get(u, {})
            if target not in self.idx:
                continue
            seen = np.zeros(len(self.movie_ids), dtype=bool)
            for m in hist:
                if m in self.idx:
                    seen[self.idx[m]] = True
            seen[self.idx[target]] = False               # the held-out film is a candidate
            cases.append((self.normalise(self.components(hist), seen), seen, self.idx[target]))
        return cases

    @staticmethod
    def metrics(cases, weights, k=10):
        """Hit rate, NDCG and MRR of ranking the held-out film among all unseen films."""
        w = np.asarray(weights, dtype=float)
        hits = ndcg = mrr = 0.0
        for norm, seen, t in cases:
            score = norm @ w
            score[seen] = -np.inf
            rank = 1 + (score > score[t]).sum() + 0.5 * ((score == score[t]).sum() - 1)
            if rank <= k:
                hits += 1
                ndcg += 1 / np.log2(rank + 1)
            mrr += 1 / rank
        n = max(len(cases), 1)
        return {"HR@%d" % k: hits / n, "NDCG@%d" % k: ndcg / n, "MRR": mrr / n, "users": len(cases)}

    def tune(self, cases, step=0.25, k=10):
        """Pick blend weights (sum to 1) that give the best NDCG on validation cases."""
        n = int(round(1 / step))
        best, best_w = -1.0, None
        for a in range(n + 1):
            for b in range(n + 1 - a):
                for c in range(n + 1 - a - b):
                    w = np.array([a, b, c, n - a - b - c]) / n
                    score = self.metrics(cases, w, k)["NDCG@%d" % k]
                    if score > best:
                        best, best_w = score, w
        self.weights = dict(zip(COMPONENTS, best_w.tolist()))
        return best


def user_auc(scores, labels):
    """AUC for one user: how often a liked film is scored above a disliked one."""
    pos = labels > 0
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = rankdata(scores)
    return (ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def _auc_cases(model, histories, test):
    """For each user: the signals of the films they actually watched later, and whether they liked them."""
    cases = []
    for u, g in test.groupby("user_id"):
        g = g[g["movie_id"].isin(model.idx)]
        labels = (g["strength"].to_numpy() > 0).astype(float)
        if len(g) < 2 or labels.min() == labels.max():
            continue
        hist = histories.get(u, {})
        seen = np.zeros(len(model.movie_ids), dtype=bool)
        for m in hist:
            if m in model.idx:
                seen[model.idx[m]] = True
        norm = model.normalise(model.components(hist), seen)
        cases.append((norm[[model.idx[m] for m in g["movie_id"]]], labels))
    return cases


def _mean_auc(cases, w):
    vals = [user_auc(m @ np.asarray(w, dtype=float), y) for m, y in cases]
    return float(np.mean([v for v in vals if v is not None])) if vals else 0.0


def _grid(step=0.25):
    n = int(round(1 / step))
    for a in range(n + 1):
        for b in range(n + 1 - a):
            for c in range(n + 1 - a - b):
                yield np.array([a, b, c, n - a - b - c]) / n


def run_auc_experiment(inter, movies, label="data", verbose=True):
    """Time split 60/20/20. Among films a user actually watched later, can we tell liked from disliked?
    Scores are per-user AUC (0.5 = coin flip, 1.0 = perfect), averaged over users."""
    inter = inter.sort_values("ts", kind="stable")
    a, b = int(len(inter) * 0.6), int(len(inter) * 0.8)
    train, val, test = inter.iloc[:a], inter.iloc[a:b], inter.iloc[b:]

    m1 = HybridRecommender().fit(train, movies)
    val_cases = _auc_cases(m1, to_histories(train), val)
    best_w = max(_grid(), key=lambda w: _mean_auc(val_cases, w))
    m1.weights = dict(zip(COMPONENTS, best_w.tolist()))

    train_val = pd.concat([train, val])
    m2 = HybridRecommender().fit(train_val, movies)
    cases = _auc_cases(m2, to_histories(train_val), test)
    rows = {"popularity": [1, 0, 0, 0], "content (TF-IDF cosine)": [0, 1, 0, 0],
            "item-KNN (cosine)": [0, 0, 1, 0], "ALS matrix factorisation": [0, 0, 0, 1],
            "hybrid (tuned blend)": best_w}
    table = pd.DataFrame({"mean user AUC": {n: _mean_auc(cases, w) for n, w in rows.items()}})
    table["users"] = len(cases)
    if verbose:
        print(f"\n{label}, liked vs disliked among later watched films ({len(cases)} users)")
        print(table.round(3).to_string())
        print("Tuned weights:", {k: round(v, 2) for k, v in m1.weights.items()})
    return table, m1.weights


def leave_last_out(inter, min_pos=4):
    """Per user: last liked film = test, second-last = validation, everything else = train."""
    pos = inter[inter["strength"] > 0].sort_values(["user_id", "ts"], kind="stable")
    users = pos.groupby("user_id").size()
    users = users[users >= min_pos].index
    last2 = pos[pos["user_id"].isin(users)].groupby("user_id").tail(2)
    test = last2.groupby("user_id").tail(1).set_index("user_id")["movie_id"].to_dict()
    val = last2.groupby("user_id").head(1).set_index("user_id")["movie_id"].to_dict()
    held = set(zip(last2["user_id"], last2["movie_id"]))
    val_pairs = set(val.items())
    keys = list(zip(inter["user_id"], inter["movie_id"]))
    is_held = np.array([k in held for k in keys])
    is_val = np.array([k in val_pairs for k in keys])
    return inter[~is_held], inter[is_val], val, test


def to_histories(df):
    out = {}
    for u, m, s in zip(df["user_id"], df["movie_id"], df["strength"]):
        out.setdefault(u, {})[m] = s
    return out


def run_experiment(inter, movies, label="data", verbose=True):
    """Full offline benchmark. Returns (results table, tuned weights, test cases info)."""
    train, val_rows, val, test = leave_last_out(inter)
    if len(test) < 10:
        raise SystemExit(f"Only {len(test)} users have enough liked films to evaluate (need 10 or more).")
    h_train = to_histories(train)

    m1 = HybridRecommender().fit(train, movies)
    m1.tune(m1.prepare_cases(h_train, val))

    # refit with the validation films included, then score on the untouched test films
    train_val = pd.concat([train, val_rows])
    h_tv = to_histories(train_val)
    m2 = HybridRecommender().fit(train_val, movies)
    m2.weights = m1.weights
    cases = m2.prepare_cases(h_tv, test)

    rows = {"popularity": [1, 0, 0, 0], "content (TF-IDF cosine)": [0, 1, 0, 0],
            "item-KNN (cosine)": [0, 0, 1, 0], "ALS matrix factorisation": [0, 0, 0, 1],
            "hybrid (tuned blend)": [m1.weights[c] for c in COMPONENTS]}
    table = pd.DataFrame({name: m2.metrics(cases, w) for name, w in rows.items()}).T
    if verbose:
        print(f"\n{label}: {len(test)} users, {len(inter)} interactions, {len(movies)} films")
        print("Held-out liked film ranked among every film the user has not seen yet.")
        print(table.round(3).to_string())
        print("Tuned weights:", {k: round(v, 2) for k, v in m1.weights.items()})
    return table, m1.weights