#!/usr/bin/env python
# coding: utf8

# jak používat T (a request, response, session, cache)
    # from gluon import current
    # ... current.T(...)

def get_stav(stav):
    return dict(p='zatím nerealizovat',
                v='výroba',
                k='kompletace',
                e='vydáno'
                )[stav]
