Title: Using Kendall's tau to compare recommendations
Date: 2016-07-12 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

### Intro

The [Kendall Tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks. It takes two ranks _that contain the same elements_ and calculates the correlation between them. A correlation of $+1$ means the ranks are equal, while a correlation of $-1$ means the ranks are exactly eachother's reverse. If two ranks are independent or randomly shuffled the correlation will be zero on average.

### Definition

The Kendall tau is defined as

$$\tau \equiv \frac{n_c - n_d}{n(n-1)/2},$$

where $n$ is the length of the ranks, $n_c$ is the number of _concordant_ pairs, and $n_d$ is the number of _discordant_ pairs.

Between two ranks $a$ and $b$, a pair of items $i$ and $j$ is

- _concordant_ if $a_i > a_j$ and $b_i > b_j$, or $a_i < a_j$ and $b_i < b_j$,
- _discordant_ If $a_i > a_j$ and $b_i < b_j$ or vice versa.
- neither _concordant_ nor _discordant_ in the case of ties, if $a_i = a_j$ or $b_i = b_j$.

### An example

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
<br>

Here $a_\text{apple} < a_\text{pear}$, while $b_\text{apple} > b_\text{pear}$, so this pair is _discordant_. 
Also, $a_\text{pear} < a_\text{banana}$ and $b_\text{pear} < b_\text{banana}$, so that pair is _condordant_.
In total, this example contains four concordant pairs and two discordant pairs. Since $n=4$, this means that
$$\tau = \frac{4-2}{6} = \frac{1}{3},$$
which means the two ranks are slightly correlated.

Please note that since there are no ties in the above example, we can directly translate it to two lists:
```python
a = ['apple', 'pear', 'banana', 'kiwi']
b = ['pear', 'banana', 'apple', 'kiwi']
```
In list-form, a concordant pair has the same order in both lists, while the order of a discordant pair is swapped. Two elements cannot occupy the same spot, so we can not have ties.

### Comparing top items

I often encounter situations where I want to compare two ranks, but where I am mostly (if not only) interested in the top end of the rank. An example of this are recommenders: a recommender of a webshop will rank all products that the webshop has to offer and then display the most relevant (let's say top-10) products on a page. So if I want to compare the results of two recommenders I might be interested in the top-10 or top-20, but I'm definitely not interested at what happens at the bottom of the lists.

Of course I can compare the top-10 results from recommender A with the top-10 results from recommender B. 
But the problem here is that the Kendall tau is not defined if the lists do not contain the same elements. And of course
the top-10 of two (very) long ranks will most likely contain some mismatched elements (if not all!).

### Ignoring mismatches

The easiest way to deal with mismatches is to ignore them. By simply removing all elements that do not occur in both
lists we reduce the problem to one that we _can_ solve. For example,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['pear', 'orange', 'banana', 'apple', 'kiwi']
```
would be reduced to the example above, where $\tau = \frac{1}{3}$. At first glance, that seems acceptable. However, in here:
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
lists `a` and `b` would be reduced to identical lists, yielding $\tau = 1$ even though the original lists are not the same.

The problems become worse when there are more mismatches in the list:
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
would _also_ evaluate to $\tau = 1$ (since `apple` and `kiwi` are concordant), while I would argue the lists are far from
equal. In the extreme case that there is only one match,
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'plum', 'orange']
```
the Kendall tau is undefined, as the denominator $n(n-1)/2 = 0$. So clearly, ignoring mismatches is not the solution to our problem.
