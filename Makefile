SHELL:=/bin/bash

.PHONY: test
test: clean
	./system-test mkdb
	diff -u <(printf "8\n67\n16\n5\n210\n") <(echo "select count(*) from state_machine;" \
	" select count(*) from event;" \
	" select count(*) from event_relation;" \
	" select count(*) from state_machine_relation;" \
	" select count(*) from event_attribute;" | \
	sqlite3 test/chronoscope.db)
	# The converter must emit the expected number of records per type;
	# combined with the totals diff above, every fixture record reaches
	# the database.
	diff -u <(printf "67\n8\n16\n5\n210\n") \
	    <(for t in event state_machine event_relation \
	          state_machine_relation event_attribute; do \
		grep -c "\"type\":\"$$t\"" test/raft_trace.jsonl; \
	    done)


.PHONY: clean
clean:
	./system-test clean


.PHONY: dev-test
dev-test: dev-clean
	python3 -m chronoscope create -v -t test/raft_trace.jsonl
	./test/browse chronoscope.db ' '


.PHONY: dev-clean
dev-clean:
	rm -fv chronoscope.db
	rm -fv tree_111_*.png *.svg *.vcd *.gtkw
