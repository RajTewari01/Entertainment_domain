.PHONY : clear_cache
clear_cache :
	python -m shortcuts.Makefile.clr_cache

.PHONY : move_logs
move_logs :
	python -m shortcuts.Makefile.mov_logs

.PHONY : pytest
pytest : 
	pytest ./tests

