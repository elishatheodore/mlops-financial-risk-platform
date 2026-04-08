# Debug Notes - Things That Broke and How I Fixed Them

## FastAPI Startup Issues
**Problem**: Server would hang indefinitely during startup  
**Cause**: Model loading was blocking the main thread  
**Fix**: Moved model loading to async context manager, but still slow  
**Status**: Partially fixed, still takes ~2 minutes on first startup

## MLflow Registry API Changes  
**Problem**: `search_model_versions` with stage filter was failing  
**Error**: `Invalid attribute key 'stage' specified`  
**Cause**: MLflow deprecated stage filtering in newer versions  
**Fix**: Filter results after fetching instead of in query  
**Lesson**: Always check MLflow version compatibility!

## Pydantic v2 Migration
**Problem**: `@validator` decorators causing import errors  
**Error**: `PydanticUserError: Decorators defined with incorrect fields`  
**Cause**: Pydantic v2 changed to `@field_validator`  
**Fix**: Updated all validators and added `@classmethod`  
**Time wasted**: ~3 hours of debugging

## Kubernetes Service Discovery
**Problem**: Pods couldn't reach each other in AKS  
**Symptoms**: Connection timeouts, DNS resolution failures  
**Cause**: Network policies too restrictive  
**Fix**: Added proper service mesh configuration  
**Lesson**: Start with permissive policies, then tighten

## Docker Multi-Arch Builds
**Problem**: Builds failing on ARM64  
**Error**: `platform linux/arm64 not supported`  
**Cause**: Missing buildx setup  
**Fix**: Used `docker/setup-buildx-action` in GitHub Actions  
**Bonus**: Now supports both AMD64 and ARM64!

## Model Registry Permissions
**Problem**: GitHub Actions couldn't access MLflow registry  
**Error**: Permission denied when promoting models  
**Cause**: Missing MLflow authentication token  
**Fix**: Added `MLFLOW_TRACKING_TOKEN` to secrets  
**Security**: Used least-privilege access

## Drift Detection False Positives
**Problem**: Constant drift alerts for normal patterns  
**Cause**: Threshold too sensitive (0.05)  
**Fix**: Adjusted to 0.15 after testing on production data  
**Monitoring**: Added alert fatigue prevention

## Memory Leaks in FastAPI
**Problem**: Memory usage increasing over time  
**Cause**: Model not being garbage collected properly  
**Fix**: Added explicit cleanup in lifespan manager  
**Tool**: Used `memory-profiler` to identify leak

## Helm Chart Validation
**Problem**: Helm dry-run passing but deployment failing  
**Error**: Invalid resource limits in production values  
**Cause**: Different resource requirements per environment  
**Fix**: Environment-specific values files  
**Lesson**: Test in staging first!

## Prometheus Metrics Not Working
**Problem**: Metrics endpoint returning 404  
**Cause**: FastAPI app mounting at wrong path  
**Fix**: Changed from `/metrics` to `/metrics` (typo!)  
**Facepalm**: Spent 2 hours on a typo

---

## Tools That Saved My Sanity
- **`kubectl logs -f`**: Real-time pod logs
- **`mlflow ui`**: Visual experiment tracking  
- **FastAPI auto-docs**: Saved API documentation time
- **Helm template debugging**: `helm template --debug`
- **Prometheus query builder**: Built-in query tester

## Time Tracking (Approximate)
- Initial setup: 2 weeks
- Debugging MLflow: 3 days  
- Kubernetes troubleshooting: 1 week
- CI/CD pipeline: 4 days
- Monitoring setup: 3 days
- Documentation: 2 days
- **Total**: ~4 weeks of part-time work

---

*These notes are for my reference - might help someone else facing similar issues!*
