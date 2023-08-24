import pandas as pd

test_csv = pd.read_csv("/mnt/input/data/test-data.csv")
test_csv.describe().to_csv("/mnt/output/test-output.csv")