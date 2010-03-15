html: $(addsuffix .html,$(basename $(wildcard *.txt) $(wildcard *.rst))) 

%.html: %.txt
	python ./rst2html --link-stylesheet --stylesheet=docutils.css --field-name-limit=0 -s -g $^ > $@.tmp && mv $@.tmp $@

%.html: %.rst
	python ./rst2html --link-stylesheet --stylesheet=docutils.css --field-name-limit=0 -s -g $^ > $@.tmp && mv $@.tmp $@

