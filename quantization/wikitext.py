from modelscope.msdatasets import MsDataset
# Load the wikitext dataset
train_datasets = MsDataset.load("wikitext", subset_name="wikitext-2-raw-v1",trust_remote_code=True)
