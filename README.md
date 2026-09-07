<<<<<<< HEAD
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

## 검증 및 제출

정답 파일이 있을 때 로컬 RMSE를 계산할 수 있습니다.

```bash
python src/score.py submission/submission_exp14.csv answer.csv
```

`hs_pred`는 유한한 수치여야 하며 0~30m 범위여야 합니다. 제출 전 열 순서와 키 중복 여부를 `src/score.py`로 확인하세요.

## 참고

KIOST 종합해양관측기지 관측자료(KORS, RS-2021-KS211502)를 사용합니다. 데이터 재배포 여부와 대회 규정은 공식 대회 사이트를 따릅니다.
=======
# p3-wave-forecast
>>>>>>> 442383adb34144fa36698035c1f5a374f83cce17
