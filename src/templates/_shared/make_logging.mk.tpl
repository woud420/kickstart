LOG_COLOR ?= \033[1;34m
LOG_RESET ?= \033[0m
ifdef NO_COLOR
LOG_COLOR :=
LOG_RESET :=
endif
log = printf "$(LOG_COLOR)==>$(LOG_RESET) %s\n" "$(1)"
