TEST_FILES := t k note5 overlap q.chop LPA DRB1-3123 chr6.C4
BASIC_TESTS := ex1 ex2
GFA_URL := https://raw.githubusercontent.com/pangenome/odgi/ebc493f2622f49f1e67c63c1935d68967cd16d85/test

# A smaller set of test inputs for faster runs.
ifdef SMALL
TEST_FILES := t k note5 overlap q.chop DRB1-3123
endif

OG_FILES := $(BASIC_TESTS:%=tests/basic/%.og) $(TEST_FILES:%=tests/%.og)
DEPTH_OG_FILES := $(OG_FILES:tests/%.og=tests/depth/%.og)

.PHONY: fetch og test clean test-all
fetch: $(TEST_FILES:%=tests/%.gfa)

og: $(OG_FILES)

test: fetch test-depth

test-depth: fetch og
	-turnt --save --env baseline tests/depth/subset-paths/*.txt
	turnt --env calyx-depth tests/depth/subset-paths/*.txt

	-turnt --save --env baseline $(DEPTH_OG_FILES)
	turnt --env calyx $(DEPTH_OG_FILES)


test-data-gen: og
	-turnt --save --env pollen_data_gen_depth_oracle tests/*.og
	turnt --env pollen_data_gen_depth_test tests/*.gfa


#################
#   slow-odgi   #
#################

# Sets up all the odgi-oracles and then tests slow-odgi against them.
test-slow-odgi: slow-odgi-setup slow-odgi-oracles slow-odgi-tests

# Produce some input files that are necessary for the slow_odgi tests.
slow-odgi-setup: og
	-turnt -j --save --env depth_setup --env inject_setup \
		--env overlap_setup --env validate_setup tests/*.gfa

# Produce the oracle output (from "real" odgi) for each test input. Run this
# once, noisily, to obtain the expected outputs. Then run `slow-odgi-tests` to
# compare against these expected outputs.
# In reality, this depends on the setup stage above. Run this by itself ONLY
# if you know that the setup stages don't need to be run afresh.
ORACLES := chop_oracle crush_oracle degree_oracle depth_oracle \
	flip_oracle flatten_oracle inject_oracle matrix_oracle overlap_oracle \
	paths_oracle validate_oracle
slow-odgi-oracles: og
	-turnt -j --save $(ORACLES:%=--env %) tests/*.og
	-turnt -j --save --env validate_oracle_err tests/invalid/*.gfa
	-turnt -j --save --env crush_oracle tests/handmade/crush*.gfa
	-turnt -j --save --env flip_oracle tests/handmade/flip*.gfa

# Test slow_odgi against the output files generated by the `slow-odgi-oracles`
# target above. Be sure to rerun that before this if the inputs or odgi
# behavior change.
TEST_ENVS := chop_test crush_test degree_test depth_test flip_test \
	 flatten_test inject_test matrix_test overlap_test paths_test validate_test
slow-odgi-tests:
	-turnt -j $(TEST_ENVS:%=--env %) tests/*.gfa
	-turnt -j --env validate_test tests/invalid/*.gfa
	-turnt -j --env crush_test tests/handmade/crush*.gfa
	-turnt -j --env flip_test tests/handmade/flip*.gfa

clean:
	rm -rf $(TEST_FILES:%=%.*)
	rm -rf $(TEST_FILES:%=tests/%.*)

	rm -rf tests/basic/*.og
	rm -rf tests/*temp.*
	rm -rf tests/depth/*.out
	rm -rf tests/depth/basic/*.out
	rm -rf tests/depth/subset-paths/*.out
	rm -rf tests/handmade/*.crush
	rm -rf tests/handmade/*.flip
	rm -rf tests/invalid/*.*

tests/%.gfa:
	curl -Lo ./$@ $(GFA_URL)/$*.gfa

%.og: %.gfa
	odgi build -g $^ -o $@
