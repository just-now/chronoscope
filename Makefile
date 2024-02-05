SHELL := /bin/bash

.PHONY: test
test: clean
	./system-test mkdb
	diff -u <(printf "629\n62\n629\n") <(echo "select count(*) from tick;" \
	" select count(*) from relation;" \
	" select count(*) from attr;" | \
	sqlite3 test/observatory.db)


.PHONY: clean
clean:
	./system-test clean
