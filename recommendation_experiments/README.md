# Recommendation Experiments

This folder is for standalone dataset export, test training, and model evaluation separate from the main Django app.

## Usage

From the project root (`Blogora_Project`):

```powershell
python recommendation_experiments\export_dataset.py
python recommendation_experiments\generate_report_assets.py
```

That script will:
- export interaction data to `recommendation_experiments/datasets/`
- export article metadata and user profile metadata as CSV
- create an aggregated training matrix CSV for recommender experiments
- create visual report assets under `recommendation_experiments/report_assets/`

## Outputs

- `datasets/interactions.csv`
- `datasets/article_metadata.csv`
- `datasets/user_profiles.csv`
- `datasets/user_article_scores.csv`
- `report_assets/interaction_event_distribution.png`
- `report_assets/top_articles_interactions.png`
- `report_assets/user_activity_distribution.png`
- `report_assets/top_categories.png`
- `report_assets/dataset_summary.csv`

## Notes

The main Django recommender trains in `apps/recommendations/train_model.py` and saves the model to `apps/recommendations/model/recommender.pkl`.

This folder is intentionally separate so you can use the exported CSV files for reporting, offline training, or external experiments.
