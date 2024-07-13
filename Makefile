SHELL:=/bin/bash

.PHONY: test
test: clean
	./system-test mkdb
	diff -u <(printf "629\n62\n629\n") <(echo "select count(*) from tick;" \
	" select count(*) from relation;" \
	" select count(*) from attr;" | \
	sqlite3 test/chronoscope.db)


.PHONY: clean
clean:
	./system-test clean


.PHONY: dev-test
dev-test: dev-clean
	python3 -m chronoscope create -t test/trace.txt -c test/chronoscope.yaml
	./test/browse chronoscope.db ' '

.PHONY: dev-clean
dev-clean:
	rm -fv chronoscope.db
	rm -fv tree_111_*.png *.svg *.vcd *.gtkw
