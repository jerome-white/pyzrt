#
# http://aclweb.org/anthology/D10-1045
# Figure 1
#

import itertools

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

msg = 'text processing vs. speech processing'

compares = [ x == y for (x, y) in itertools.combinations(msg, 2) ]

dot = np.ones([ len(msg) ] * 2)
dot[np.triu_indices(len(msg), 1)] = compares
dot = np.transpose(np.fliplr(np.triu(dot)))

ax = sns.heatmap(dot, xticklabels=list(msg), yticklabels=list(msg[::-1]))
plt.savefig('aren.png')
