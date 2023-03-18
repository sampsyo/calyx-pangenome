TEST_FILES := t k note5 overlap q.chop DRB1-3123 LPA
BASIC_TESTS := ex1 ex2
OG_FILES := $(BASIC_TESTS:%=test/basic/%.og) $(TEST_FILES:%=test/%.og)
DEPTH_OG_FILES := $(OG_FILES:test/%.og=test/depth/%.og)
GFA_URL := https://raw.githubusercontent.com/pangenome/odgi/ebc493f2622f49f1e67c63c1935d68967cd16d85/test
GFA_ZIP_URL := https://s3-us-west-2.amazonaws.com/human-pangenomics/pangenomes/scratch/2021_05_06_pggb/gfas/chr8.pan.gfa.gz

.PHONY: fetch og test clean test-all
fetch: $(TEST_FILES:%=test/%.gfa)

og: $(OG_FILES)

test: og test-depth

test-depth: og
	-turnt --save --env baseline test/depth/subset-paths/*.txt
	turnt test/depth/subset-paths/*.txt

	-turnt --save --env baseline $(DEPTH_OG_FILES)
	turnt $(DEPTH_OG_FILES)

test-slow-odgi: og test-slow-chop test-slow-crush test-slow-degree test-slow-depth test-slow-emit
# to add: test-slow-flip

test-slow-chop: og
	-turnt --save --env chop_oracle test/*.og
	turnt --env chop_test test/*.gfa

test-slow-crush: og
	-turnt --save --env crush_oracle test/*.og
	turnt --env crush_test test/*.gfa

test-slow-degree: og
	-turnt --save --env degree_oracle test/*.og
	turnt --env degree_test test/*.gfa

test-slow-depth: og
	-turnt --save --env depth_oracle test/*.og
	turnt --env depth_test test/*.gfa

test-slow-emit: og
	-turnt --save --env emit_oracle test/*.og
	turnt --env emit_test test/*.gfa

test-slow-flip: og
	-turnt --save --env flip_oracle test/*.og
	turnt --diff --env flip_test test/*.gfa

test-slow-matrix: og
	-turnt --save --env matrix_oracle test/*.og
	turnt --diff -v --env matrix_test test/*.gfa

test-slow-validate: fetch
	-turnt --save --env validate_setup/*.gfa
	-turnt -v --save --env validate_oracle test/*.gfa
	# turnt --diff -v --env validate_test test/*.gfa


clean:
	rm -rf $(TEST_FILES:%=%.*)
	rm -rf $(TEST_FILES:%=test/%.*)

	rm -rf test/basic/*.og

	rm -rf test/temp.*
	rm -rf test/depth/*.out
	rm -rf test/depth/basic/*.out
	rm -rf test/depth/subset-paths/*.out

test/chr8.pan.gfa:
	curl -Lo ./test/chr8.pan.gfa.gz $(GFA_ZIP_URL)
	gunzip ./test/chr8.pan.gfa.gz

test/%.gfa:
	curl -Lo ./$@ $(GFA_URL)/$*.gfa

%.og: %.gfa
	odgi build -g $^ -o $@
