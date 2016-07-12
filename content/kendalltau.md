Title: Using Kendall's tau to compare recommendations
Date: 2016-07-12 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

## Intro

The [Kendall Tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks. It compares every _pair_ of items between the ranks

## Definition

The Kendall tau is defined as

$$\tau \equiv \frac{n_c - n_d}{n(n-1)/2},$$

where $n$ is the length of the ranks, $n_c$ is the number of _concordant_ pairs, and $n_d$ is the number of _discordant_ pairs.

A pair of items $i$ and $j$ is _concordant_ between two ranks $a$ and $b$ if $a_i > a_j$ and $b_i > b_j$, or $a_i < a_j$ and $b_i < b_j$. If $a_i > a_j$ and $b_i < b_j$ or vice versa, the pair is _discordant_. In the case of ties, if $a_i = a_j$ or $b_i = b_j$, the pair is neither _concordant_ nor _discordant_.

## An example

Let's have a look at these two ranks:

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>rank_a</th>
      <th>rank_b</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>apple</th>
      <td>1</td>
      <td>3</td>
    </tr>
    <tr>
      <th>banana</th>
      <td>3</td>
      <td>2</td>
    </tr>
    <tr>
      <th>pear</th>
      <td>2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>kiwi</th>
      <td>4</td>
      <td>4</td>
    </tr>
  </tbody>
</table>
</div>

Here $a_\text{apple} < a_\text{pear}$, while $b_\text{apple} > b_\text{pear}$, so this pair is _discordant_. 
Also, $a_\text{pear} < a_\text{banana}$ and $b_\text{pear} < b_\text{banana}$, so that pair is _condordant_.
In total, this example contains four concordant pairs and two discordant pairs. Since $n=4$, this means that
$$\tau = \frac{4-2}{6} = \frac{1}{3},$$
which means the two ranks are slightly correlated.

Please note that since there are no ties in the above example we can directly translate it to two lists:
```python
a = ['apple', 'pear', 'banana', 'kiwi']
b = ['pear', 'banana', 'apple', 'kiwi']
```

## Comparing recommendations

A problem arises when one tries to compare recommendations. A recommender often comes up with a _very_ long list of all possible items, while we are only interested in a few items at the top. 

For example, a recommender of a webshop will rank all products that are available in the shop, and then show the best (let's say top-5) as suggestions. If we want to compare the output of two recommenders we are not interested in the correlation of the _entire_ ranks, since only the 5 best results are shown.

One would want to compare only the top-5 results of each recommender. The problem here lies in the fact that the Kendall tau is undefined if the two ranks do not contain the same elements. And if we are comparing two recommenders which each pick 5 items from a very large set, then it is likely that there are some items that do not occur is both lists, if not all.

## 
