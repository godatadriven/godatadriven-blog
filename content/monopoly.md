Title: What we can learn about data and marketing from Monopoly
Date: 2015-12-24 15:00
Slug: monopoly
Author: Walter van der Scheer
Excerpt: Create your own monopoly this holiday season in four simple steps. Benefit from the insights that GoDataDriven got based on a simulation of the Monopoly board game.
Template: article
Latex:

<span class="lead">With the holidays just around the corner it is the season to be jolly. Chances are likely that besides some big meals you will also come across a game of Monopoly. Data scientist Vincent Warmerdam decided that no longer he accepted going bankrupt on a hotel in some small village, like Mediterranean avenue (De Brink, Ons Dorp in the Dutch game of Monopoly). So, he decided to use his data skills to create the ultimate Monopoly strategy. Using his insights, this year it is your turn to build your own monopoly over Christmas.</span>

![Monopoly: data and marketing](/static/images/monopoly/1-godatadriven-monopoly-jail.jpg)

## Monopoly as a serious game

Monopoly exists exactly 80 years and can be seen as one of the first serious games. The American anti-monopolist and feminist Elizabeth Philips-Magie invented a first version in 1903 to point out that a monopoly leads to an unfair division of wealth. Eventually a smart business man ran away with Philips-Magie’s game concept and gained substantial wealth with it. How ironic.

## Improve your odds by taking the right strategic decisions

Staying ahead of competition by using smart analysis, making smart investments and adapting to market changes quickly. Monopoly is just like conquering markets in real-life.

In this article we combine a simulation of Monopoly and data to create insights to optimize our chances to end the game as a winner. We did simplify the rules a bit, though; We mostly look at the probability to land on a certain street and don’t take the cash of a player into account. Besides that, we have not looked at the influence of cards from the Community Chest and Chance piles.

For the simulation and analysis, we have used open source language Python to play 100 games with 1000 players.

## 1: Stay away from jail

Chances to end up in jail are no less than 5 times higher than to land on any other tile. Only by throwing doubles you can leave prison, so most players land on a tile that is an even amount away from jail. These are Electric Company (elektriciteitsbedrijf), States Avenue (Houtstraat), St. James Place (Neude), Tennessee Avenue (Biltstraat), Free Parking (Vrij Parkeren) and Chance (Kans).

![Monopoly: distribution](/static/images/monopoly/2-godatadriven-monopoly-distribution.png)

## 2: Pick the right streets

What streets represent the highest value? First of all we took a look at the train stations. The probability to land on Station West and Station East is about 5% higher than the other two stations. Count your profit!

Looking at the streets, the colors Orange (Utrecht), Yellow (Den Haag) and Red (Groningen) have the highest probability. Chances to land on the Blue (Amsterdam) and Purple (Ons Dorp) streets are lower, partly because in the game these colors contain only two streets.

![Monopoly: best streets](/static/images/monopoly/3-godatadriven-monopoly-board.jpg)

Based on the revenues of a deed without houses / hotels we have made a calculation of the expected income from rent, compared to the probability of a player landing on this street, which we visualized in a plot. The larger the circle, the higher the revenue. What stands out is that a number of streets have a low revenue and a low probability.

![Monopoly: probability](/static/images/monopoly/4-godatadriven-monopoly-revenues-probability.png)

A closer examination points out that especially the streets that are difficult to reach coming from jail, brown (Ons Dorp), light blue (Arnhem) and pink (Haarlem), see lower revenues. Green (Rotterdam) and dark Blue (Amsterdam) have the highest estimated revenues

## 3: Go for maximum return on investment

How many turns are needed to get a positive return on investment via rental revenues and by placing houses and hotels? Mediterranean Avenue (Dorpsstraat, Ons Dorp) is the least attractive street, as it takes 30 visits to earn your investment back from rent, which is at least double as much as for the other streets. Boardwalk has earned itself back already after 8 players have paid their rents due. Investing in a hotel is the fastest way to earn back your investment.

When we take the probability of landing on a certain street, we see that the investment in Mediterranean Avenue is returned only after 732 turns and Boardwalk already in 196 turns.

![Monopoly: highest number of turns for positive ROI](/static/images/monopoly/5-godatadriven-highestnumber.png)

If you are after as much revenue from rent as possible, staying away from the Pink streets (Arnhem) is a wise thing to do, as only Mediterranean Avenue (Dorpsstraat, Ons Dorp) takes longer to earn back your investment. Interestingly you earn back your investment from a hotel relatively quickly with a Pink street (Arnhem). Another interesting observation is that the performance of Park Place (Leidsestraat, Amsterdam) is notably worse than that of its neighboring street Boardwalk. 

![Monopoly: lowest number of turns for positive ROI](/static/images/monopoly/6-godatadriven-lowestnumber.png)

## 4: The winning strategy

The best strategy to end the game a winner? Orange, Yellow, and Red streets usually see a steady visitor, and thus revenue, stream. Higher numbered streets, the streets from jail to start, give a better profit probability. It is not necessary to focus on the Orange, Yellow, and Red streets alone, obtaining as many streets as possible early in the game is the best tactic. Other players that are looking to complete their colors, will be open to trading cards later in the game.

Buy your houses on the Orange, Yellow, and Red streets first. Only buy hotels when you have sufficient cash to put the houses back on other street. As long as you own all the houses, the streets of other players are virtually worthless. Three houses on a street give the optimum investment versus revenue ration. 

## 5: Conclusion

The data analytic insights based on this simulation provide valuable insights to improve your game effectiveness. Use the insights to create the winning tactic and become the monopolist amongst your friends and family. Success is indeed a choice. Before you decide to become Rich Uncle Penny Bags, ask yourself the question: do you play for the hard bucks or the fun? Happy Holidays!

