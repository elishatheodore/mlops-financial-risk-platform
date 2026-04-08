# TODO List - Things I Still Need to Fix

## High Priority
- [ ] Fix the drift detection timing - currently hardcoded to 6 hours, should be configurable
- [ ] Add better error handling in FastAPI when model loading fails
- [ ] Implement proper retry logic for MLflow registry calls
- [ ] Add input validation for edge cases (negative amounts, etc.)

## Medium Priority  
- [ ] Set up proper logging instead of just print statements
- [ ] Add integration tests for the full pipeline
- [ ] Implement model version comparison before promotion
- [ ] Add rate limiting to prevent API abuse

## Low Priority (Nice to have)
- [ ] Add SHAP values for model explainability
- [ ] Implement A/B testing framework for model comparison
- [ ] Set up proper feature store (currently using numpy arrays)
- [ ] Add model fairness metrics and monitoring

## Known Issues
- **Model loading is slow**: First startup takes ~2 minutes to download artifacts from MLflow
- **Memory usage**: Could be optimized for large datasets
- **Pydantic warnings**: Still getting some deprecation warnings, need to clean up

## Things I Tried That Didn't Work
1. **Streaming predictions with Kafka**: Too complex for this use case, batch is fine
2. **Deep learning models**: Overkill for tabular fraud data, tree models work better
3. **Custom monitoring solution**: Prometheus is actually pretty good once you learn it

## Future Ideas
- Real-time fraud detection with streaming data
- Multi-model ensemble for better accuracy  
- Automated hyperparameter tuning with Optuna
- Graph database for transaction relationship analysis

---

*Last updated: 2024-04-08*
*Note: This is my personal TODO list - some items might not make sense to others!*
