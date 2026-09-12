# Scientific methods and interpretation

## Binary coefficient

For threshold \(k\), let \(N_{>k}\) be the number of nodes with degree greater
than \(k\), and let \(E_{>k}\) be the number of edges among those nodes. RichClub
Explorer calculates

$$
\phi(k)=\frac{2E_{>k}}{N_{>k}(N_{>k}-1)}.
$$

This is the density of the subgraph induced by nodes richer than the threshold.

## Null ensemble

Each binary null network is generated through double-edge swaps. This preserves
the number of nodes, number of edges, and degree of every node while randomizing
which node pairs are connected. The default is ten attempted swaps per edge.

The application compares the observed coefficient with \(B\) null coefficients
at every threshold:

$$
\rho(k)=\frac{\phi_{\mathrm{obs}}(k)}
{B^{-1}\sum_{b=1}^{B}\phi^{(b)}_{\mathrm{null}}(k)}.
$$

The empirical one-sided p-value uses a plus-one correction:

$$
p(k)=\frac{1+\sum_{b=1}^{B}
\mathbf{1}\left[\phi^{(b)}_{\mathrm{null}}(k)\geq
\phi_{\mathrm{obs}}(k)\right]}{B+1}.
$$

At least 1,000 null networks are recommended for final analyses. Ten to one
hundred nulls are useful only for rapid exploration.

## Weighted coefficient

The exploratory weighted mode reports the sum of weights among rich nodes divided
by the sum of the globally strongest \(E_{>k}\) edge weights. Null networks preserve
the degree sequence and randomly permute the observed weights over rewired edges.
This preserves the global weight distribution but not individual node strengths.
Accordingly, a strength-preserving scientific question requires a more specialized
null model than v0.1 provides.

## Interpretation safeguards

Rich sets are nested across thresholds, so neighboring tests are strongly dependent.
An isolated threshold with \(\rho(k)>1\) should not be interpreted as definitive
rich-club organization. A defensible result should consider:

- the observed coefficient relative to the full null distribution
- persistence over a meaningful range of thresholds
- the number of nodes retained at each threshold
- robustness to network construction, density, and preprocessing
- the specific rich nodes and rich-club edges involved
- the relationship between the chosen null model and the biological hypothesis

The software flags thresholds retaining fewer than five rich nodes by default.
This threshold is a visibility safeguard, not a universal statistical rule.

## Edge classes

At a selected richness threshold, edges are classified as:

- **Rich-club:** both endpoints belong to the rich set
- **Feeder:** one endpoint belongs to the rich set
- **Local:** neither endpoint belongs to the rich set

These classifications describe topology at the selected threshold and do not imply
causality or biological function.

## Suggested reporting checklist

Report the network type, construction rule, node and edge counts, density, richness
definition, threshold range, null-model constraints, number of null networks,
rewiring intensity, random seed, minimum retained-node rule, software version,
and all sensitivity analyses. Provide node membership and edge classifications as
supplementary tables whenever possible.

## Foundational references

- Colizza V, Flammini A, Serrano MA, Vespignani A. Detecting rich-club ordering in
  complex networks. *Nature Physics*. 2006;2:110–115.
- Maslov S, Sneppen K. Specificity and stability in topology of protein networks.
  *Science*. 2002;296:910–913.
- Opsahl T, Colizza V, Panzarasa P, Ramasco JJ. Prominence and control: The weighted
  rich-club effect. *Physical Review Letters*. 2008;101:168702.
- van den Heuvel MP, Sporns O. Rich-club organization of the human connectome.
  *Journal of Neuroscience*. 2011;31:15775–15786.
