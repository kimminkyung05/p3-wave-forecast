"""문제 3 채점 — 유의파고 RMSE (엄격 입력 검증 포함)"""
import sys
import numpy as np
import pandas as pd

if len(sys.argv) != 3:
    raise SystemExit("사용법: python score.py submission.csv answer.csv")

sub = pd.read_csv(sys.argv[1])
ans = pd.read_csv(sys.argv[2])
K = ["case_id", "station", "lead_h"]
required = K + ["hs_pred"]

if list(sub.columns) != required:
    raise SystemExit(f"열 이름/순서 오류: {list(sub.columns)}; 필요: {required}")
if not set(K + ["hs"]).issubset(ans.columns):
    raise SystemExit("정답 파일 스키마 오류")
if len(sub) != len(ans):
    raise SystemExit(f"행 수 오류: 제출 {len(sub):,} / 정답 {len(ans):,}")
if sub[K].isna().any().any():
    raise SystemExit("제출 키에 결측이 있습니다")
if sub.duplicated(K).any():
    raise SystemExit(f"제출 키 중복 {int(sub.duplicated(K).sum()):,}건")
if ans.duplicated(K).any():
    raise SystemExit("정답 키 중복")
if not sub["lead_h"].isin([3, 6, 9, 12, 18, 24]).all():
    raise SystemExit("lead_h는 3, 6, 9, 12, 18, 24만 허용합니다")

try:
    m = ans[K + ["hs"]].merge(sub, on=K, how="outer", indicator=True,
                                validate="one_to_one")
except Exception as e:
    raise SystemExit(f"키 검증 실패: {e}")
if not m["_merge"].eq("both").all():
    raise SystemExit(f"키 집합 불일치: 누락/초과 {int(m['_merge'].ne('both').sum()):,}건")

p = pd.to_numeric(m["hs_pred"], errors="coerce")
if p.isna().any() or not np.isfinite(p.to_numpy()).all():
    raise SystemExit("hs_pred는 결측 없는 유한한 숫자여야 합니다")
if not p.between(0.0, 30.0).all():
    raise SystemExit("hs_pred 허용 범위는 0~30 m입니다")

m["hs_pred"] = p
e = m["hs_pred"].to_numpy() - m["hs"].to_numpy()
print(f"RMSE = {np.sqrt(np.mean(e**2)):.6f} m  (n={len(m)})")
for lead, g in m.groupby("lead_h"):
    print(f"  +{int(lead)}h : {np.sqrt(np.mean((g.hs_pred-g.hs)**2)):.6f}")
for station, g in m.groupby("station"):
    print(f"  {station} : {np.sqrt(np.mean((g.hs_pred-g.hs)**2)):.6f}")
