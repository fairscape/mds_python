# TODO

## CLI Implementation


### Running in a local environment

Run a single process
```bash
# register input datasets
DATASET_ID=`fairscape register dataset \
	--name "Music Test" \
	--author "orchid.org/0000-0000-0000-0000"
	...`


# register software
SOFTWARE_ID = `fairscape register software \
	--author "orcid.org/0000-000-"`

# single 
# run computation
COMPUATATION_ID = `fairscape register computation \
	--usedSoftware ... \
	--usedDatasets ["ark:99999/input-data"]`


# run music 
music pipeline command

# register the output datasets
OUTPUT_IDS= `fairscape register dataset \
	--generatedBy $COMPUTATION_ID \
	`
```

Execute 
```bash

fairscape upload datasets ...

fairscape upload software ...

fairscape execute computation \
	--usedDatasets ["ark:99999/test-dataset"] \
	--usedSoftware "ark:99999/" \
	--image "python3" --resources
```