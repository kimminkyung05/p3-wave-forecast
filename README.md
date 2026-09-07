# P3 Wave Forecast

2026 해양과학 AI·빅데이터 경진대회 온라인 해커톤의 문제 3, **종합해양관측기지 유의파고 예측** 프로젝트입니다. 48시간 관측 문맥을 바탕으로 +3, +6, +9, +12, +18, +24시간의 유의파고(`hs`)를 예측합니다.

- 대회 사이트: [oceanaidata.org](https://oceanaidata.org/)
- 평가: 모든 관측소·리드타임을 통합한 RMSE (m)
- 제출 열: `case_id, station, lead_h, hs_pred`

## 프로젝트 구조

```text
.
├── data/
│   ├── raw/              # 대회 원본 관측·테스트 데이터
│   ├── processed/        # 전처리·피처 생성 학습 데이터
│   └── reference/        # sample submission, baseline
├── experiments/          # 실험 및 전처리 노트북
│   └── preprocessing/
├── artifacts/experiments/ # 노트북 실행으로 생성되는 모델·Optuna 결과
├── oof/                  # OOF 예측 결과
├── submission/           # 대회 제출 CSV
├── configs/              # 실험별 최적 하이퍼파라미터
├── src/                  # 재사용 가능한 파이프라인·평가 코드
└── archive/              # 레거시 노트북과 원본 배포 묶음 사본
```

`data/` 전체는 `.gitignore` 대상입니다. 대회 원본과 전처리 데이터는 저장소에 커밋하지 않고 각 실행 환경에 로컬로 준비합니다. 실험 산출물은 `artifacts/experiments/`로, 제출 파일은 `submission/`으로 저장합니다.

## 빠른 시작

1. [대회 사이트](https://oceanaidata.org/)에서 제공받은 데이터를 아래 위치에 배치합니다.

   ```text
   data/raw/train_atmos.csv
   data/raw/train_wave.csv
   data/raw/test_context.parquet
   data/raw/test_index.csv
   data/reference/sample_submission.csv
   ```

2. 초기 전처리 파이프라인을 실행합니다.

   ```bash
   python src/train_pipeline.py
   ```

3. `experiments/`의 해당 노트북을 실행합니다. 노트북은 프로젝트 루트를 자동으로 찾고 `data/`, `oof/`, `submission/`, `artifacts/` 경로를 사용하도록 정리되어 있습니다.

## 데이터

| 위치 | 내용 |
|---|---|
| `data/raw/train_wave.csv` | 파랑 관측 데이터 |
| `data/raw/train_atmos.csv` | 기상 관측 데이터 |
| `data/raw/test_context.parquet` | 테스트 예측 문맥 |
| `data/raw/test_index.csv` | 테스트 예측 인덱스 |
| `data/processed/train_final_physics_v*.csv` | 실험용 피처 데이터셋 |
| `data/reference/sample_submission.csv` | 제출 형식 예시 |

`data/processed/`의 파일은 `src/train_pipeline.py` 또는 전처리 노트북으로 생성·갱신합니다. 대회 데이터의 재배포는 하지 않습니다.

## 최종 선택 구성

최종 제출 기준 조합은 **EXP04 iTransformer + V4 전처리 데이터**입니다.

| 구성 요소 | 선택 |
|---|---|
| 모델 | `experiments/exp04.ipynb` — iTransformer + Competition-Aligned Weighted RMSE Loss |
| 학습 데이터 | `data/processed/train_final_physics_v4.csv` |
| 데이터 생성 | `experiments/preprocessing/train_v4.ipynb` |
| 재현 노트북 | `experiments/FINAL_REPRO_EXP04.ipynb` |
| 제출 산출물 | 기본 실행: `submission/submission_exp04.csv` · 재현 노트북: `submission/submission_exp04_final.csv` |

## 실험 기록

모든 예측 실험은 기본적으로 과거 48시간(289 step) 문맥에서 `+3/+6/+9/+12/+18/+24h` 유의파고를 예측합니다. `OOF`는 앙상블 가중치 탐색용 Out-of-Fold 예측이며, 표의 산출물은 실행 시 `oof/`, `submission/`, 또는 `artifacts/experiments/`에 생성됩니다.

| 실험 | 모델·목적 | 핵심 특징 | 주요 산출물 |
|---|---|---|---|
| EXP01 | iTransformer | 물리 피처 그룹 선택과 모델 하이퍼파라미터를 Optuna로 동시 탐색 | `submission_exp01.csv` |
| EXP02 | iTransformer | 피처 그룹 ablation, feature set별 usable window 검증, 시간 순서 검증 | `submission_exp02.csv` |
| EXP03 | iTransformer | 파고 모멘텀·에너지·풍응력 피처 확장, 고파랑 가중 MSE | `submission_exp03.csv` |
| EXP04 | iTransformer | 대회 정렬 가중 RMSE 손실, 78시간 독립 간격 검증 | `oof_exp04.csv`, `submission_exp04.csv` |
| EXP05 | LightGBM | 48시간 통계·모멘텀 tabular 피처, 리드타임별 5-Fold·Optuna | `oof_exp05.csv`, `submission_exp05.csv` |
| EXP06 | XGBoost | EXP05와 같은 direct multi-target 설계의 XGBoost GPU/Hist 변형 | `oof_exp06.csv`, `submission_exp06.csv` |
| EXP07 | CatBoost | EXP05와 같은 direct multi-target 설계의 CatBoost GPU 변형 | `oof_exp07.csv`, `submission_exp07.csv` |
| EXP08 | GBDT 블렌딩 | EXP05~07 OOF를 SLSQP로 리드타임별 최적 가중 블렌딩 | `oof_exp08.csv`, `submission_exp08.csv` |
| EXP09 | GBDT 스태킹 | 리드타임별 블렌딩 + non-negative Ridge 메타모델 + 고파랑 보정 | `oof_exp09.csv`, `submission_exp09.csv` |
| EXP10 | PatchTST | 시계열 패치 임베딩, 피처 ablation, 대회 정렬 가중 손실·Optuna | `oof_exp10.csv`, `submission_exp10.csv` |
| EXP11 | 딥러닝 앙상블 | EXP04 iTransformer와 EXP10 PatchTST의 OOF 최적 가중 결합 | `oof_exp11.csv`, `submission_exp11.csv` |
| EXP12 | TCN | Causal Dilated Convolution으로 긴 문맥과 피크 변화를 학습 | `submission_exp12.csv` |
| EXP13 | TCN | 정확한 78시간 독립 피크 지표와 비대칭 피크 손실 적용 | `submission_exp13.csv` |
| EXP14 | iTransformer | EXP04 대회 정렬 손실·물리 피처 구성을 재실행한 비교 실험 | `submission_exp14.csv` |
| EXP15 | iTransformer + V5 | 완전 시간 그리드, 기준·타깃 피크 인지 손실, Exact 78h 최적화 | `submission_exp15.csv` |
| EXP16 | iTransformer + V5 | 고파랑 adaptive stride와 대치값 감쇠 peak loss | `submission_exp16.csv` |
| EXP17 | TCN + V5 | 완전 시간 그리드 기반 TCN, Exact 78h 최적화 | `oof_exp17_tcn.csv`, `submission_exp17_tcn.csv` |
| EXP18 | TimesNet + V5 | FFT 기반 다중 주기·국소 피크 포착, Exact 78h 최적화 | `oof_exp18_timesnet.csv`, `submission_exp18_timesnet.csv` |
| EXP19 | iTransformer + V5 | 비대칭 피크 손실과 기압·에너지·풍력 가속도 피처 | `oof_exp19.csv`, `submission_exp19.csv` |
| EXP20 | iTransformer + V5 | 앵커 기반 전진 피처 선택과 비대칭 피크 손실 | `oof_exp20.csv`, `submission_exp20.csv` |
| EXP24 | iTransformer + V6 | target-aware 고파랑 손실, causal 추론, dual-seed 앙상블 | `submission_exp24_ensemble.csv` |
| EXP25 | iTransformer 앙상블 | Storm Physics·Wave Momentum/Wind 이종 피처셋의 독립 Optuna HPO | `submission_exp25_ensemble.csv` |
| EXP26 | iTransformer | 순수 RMSE 손실, `comp_rmse` 조기 종료, causal 추론·Optuna | `submission_exp26.csv` |
| EXP26 Dual | iTransformer 앙상블 | 두 이종 피처셋 + Pure RMSE + 검증 기반 dynamic blending | `submission_exp26_dual_pure_ensemble.csv` |
| EXP26 Full Optuna | iTransformer 앙상블 | 두 모델의 독립 Optuna HPO 후 최적 가중 블렌딩 | `submission_exp26_optuna_ensemble.csv` |
| EXP_LOSS | 손실 함수 ablation | Target-aware·연속 가중·비대칭·Pure RMSE 손실 비교 | 실험 결과는 `artifacts/experiments/` |
| FINAL_REPRO_EXP04 | 최종 재현 | 공식 원본 데이터부터 EXP04 학습·추론까지 한 번에 재현 | `submission_exp04_final.csv` |

### 전처리 노트북

| 노트북 | 역할 | 주요 산출물 |
|---|---|---|
| `preprocessing/train_v2.ipynb` | 원본 파랑·기상 데이터 병합 및 초기 피처 전처리 | V2 기반 학습 데이터 |
| `preprocessing/train_v3.ipynb` | 중간 산출물을 메모리에서 처리하는 최종 물리 피처 파이프라인 | `train_final_physics_v3.csv` |
| `preprocessing/train_v4.ipynb` | 관측 mask를 보존한 안전한 물리 피처 생성 | `train_final_physics_v4.csv` |
| `preprocessing/train_v5.ipynb` | 10분 균일 그리드·결측 복원·물리 파생변수 생성 | `train_final_base_v5.csv`, `train_final_physics_v5.csv` |
| `preprocessing/train_v6.ipynb` | V5 후속 전처리 및 V6 물리 피처셋 생성 | `train_final_base_v6.csv`, `train_final_physics_v6.csv` |

## 검증 및 제출

정답 파일이 있을 때 로컬 RMSE를 계산할 수 있습니다.

```bash
python src/score.py submission/submission_exp14.csv answer.csv
```

`hs_pred`는 유한한 수치여야 하며 0~30m 범위여야 합니다. 제출 전 열 순서와 키 중복 여부를 `src/score.py`로 확인하세요.

## 참고

KIOST 종합해양관측기지 관측자료(KORS, RS-2021-KS211502)를 사용합니다. 데이터 재배포 여부와 대회 규정은 공식 대회 사이트를 따릅니다.
