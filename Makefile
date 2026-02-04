# Makefile
# 
.PHONY: deploy
deploy:
	gcloud run deploy remindanyone --source=. --project=remindanyone --region=europe-central2