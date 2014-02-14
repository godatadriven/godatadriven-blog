Title: Some recommendations in Neo4j
Date: 2014-01-30 10:00
Slug: some-recommendations-in-neo4j
Author: Friso van Vollenhoven
Excerpt: Graphs are nice. You can model almost anything with them and they are easy to reason about and allow for great exploratory analysis. <a href="http://www.neo4j.org/">Neo4j</a> is a developer and user friendly graph database, which offers a declarative query language called <a href="http://www.neo4j.org/learn/cypher">Cypher</a>. In this post we'll explore how far we can get to a working recommendation engine using only Neo4j and Cypher. We implement a naïve Bayes classifier and collaborative filtering based on item-item cosine similarity purely in Cypher.
Template: article

Not so long ago, I attended [Graph Café](http://www.meetup.com/graphdb-netherlands/events/155371722/ "Graph Café"), a nice type of meetup where there is no formal agenda, but there is just a series of lightning talks with beer inspired breaks in between. Graph Café's are organized every so often by the [Graph Database - Amsterdam meetup group](http://www.meetup.com/graphdb-netherlands/). Naturally, my friend [Rik van Bruggen](https://twitter.com/rvanbruggen "Rik van Bruggen on Twitter"), kindly and without any pressure had asked me to also do a lightning talk, so I had to come up with something. Neo4j 2.0 was released recently and the Graph Café was actually for celebrating this occasion. One of the new features in 2.0 is a major overhaul of the Cypher query language. I wanted to find out how much you could do with the query language in terms of creating functionality. My challenge: implement different forms of recommendations purely in Cypher. And I'm not talking about the basic co-occurrence counting type of recommendations, but something less trivial than that. My lightning talk ended up being about creating a [naïve Bayes classifier](http://en.wikipedia.org/wiki/Naive_Bayes_classifier "Naïve Bayes Classifier on Wikipedia") in Cypher, which kind of worked. Obviously, I couldn't just leave it at that, so now I implemented the classifier and collaborative filtering (based on item-item cosine similarity) purely in Cypher. This post explains how.


### Your Meetup.com neighborhood in a graph
In order to do recommendations, we need a dataset with things in it that can be recommended. For this, I chose to grab data for a number of Meetup.com groups through their [excellent API](http://www.meetup.com/meetup_api/ "The Meetup.com API"). This allows us to retrieve groups, their members, the members' RSVP's, the members' interests and much more. Our graph contains several meetup groups with all members, topics that are of interest to members and to groups and all RSVP's by members for each group. These are the possible relations and node labels (if this look awkward to you, go [read about Cypher](http://www.neo4j.org/learn/cypher) first):

    :::cypher
    (member:Member)-[:HAS_MEMBERSHIP]->(group:Group)
    (member:Member)-[:LIKES]->(topic:Topic)
    (member:Member)-[:RSVP_ED]->(event:Event)

    (group:Group)-[:ORGANISED]->(event:Event)
    (group:Group)-[:DISCUSSES]->(topic:Topic)

The graph is built using a simple Python script that makes the required API calls and populates the database using [py2neo](http://nigelsmall.com/py2neo "Thanks Nigel!"). Before we can do useful matching against the database, we need to create some indexes, so we can find things by name. Luckily, in the new Cypher, this is super easy!

    :::cypher
    create index on :Group(name)
    create index on :Member(name)
    create index on :Topic(name)

Now, let's find me (Friso van Vollenhoven) and show all my group memberships, the topics I like, the topics my groups discuss and the events that I RSVP'ed for:
![meetup graph](static/images/some-recommendations-in-neo4j/meetup-graph.png)


### Are you a graph database person?
In our example, we are going to look for people that we can recommend the Graph Database - Amsterdam meetup group to. Basically, for each person in the database, we are going to ask: are you a graph database person? And we will try to predict who would answer yes to that question. Those people will be the ones we can recommend the graph database group to.

One way of recommending items to users is to determine the probability that a user is going to convert on the item. Converting means the user is buying a product, joining a group, registering for a service, or whatever else your target is. In our case, we are going to determine whether a user has 

    :::cypher
    # Get total # of members
    match
      (member:Member)-[:HAS_MEMBERSHIP]->(grp:Group)
    return
      count(distinct member) as total_members

x

    :::text
     total_members 
    ---------------
     3191          
    (1 row)
x

    :::cypher
    # Get # of graph DB group members
    match
      (grp:Group { name: 'Graph Database - Amsterdam'})<-[:HAS_MEMBERSHIP]-(member:Member)
    return
      count(distinct member)

x

    :::text
     count(distinct member) 
    ------------------------
     240                    
    (1 row)

x

    :::cypher
    # Set global # of likes on each topic
    match
      (topic:Topic)<-[:LIKES]-(member:Member)
    with
      topic, count(distinct member) as likes
    set
      topic.like_count = likes + 1
    return
      count(topic)

x

    :::text
     count(topic) 
    --------------
     3643         
    (1 row)

x

    :::cypher
    # Set # of likes from graph DB members on each topic
    match
      (grp:Group { name:'Graph Database - Amsterdam'} )<-[:HAS_MEMBERSHIP]-(member:Member)-[:LIKES]->(topic:Topic)
    with
      topic, count(distinct member) as likes
    set
      topic.graphdb_like_count = likes + 1
    return
      count(topic)

x

    :::text
     count(topic) 
    --------------
     778          
    (1 row)

x

    :::cypher
    # Set # of likes from members NOT IN graph DB group
    match (graphdb:Group { name:'Graph Database - Amsterdam' }), (other:Group)<-[:HAS_MEMBERSHIP]-(member:Member)-[:LIKES]->(topic:Topic)
    where not graphdb<-[:HAS_MEMBERSHIP]-member
    with topic, count(distinct member) as likes
    set topic.non_graphdb_like_count = likes + 1
    return count(topic)

x

    :::text
     count(topic) 
    --------------
     3508         
    (1 row)

x

    :::cypher
    # Per feature probs for some member
    match
      (member:Member { name : 'Rik Van Bruggen' })-[:LIKES]->(topic:Topic)
    return
      topic.name,
      coalesce(topic.graphdb_like_count, 1.0) / 240.0 as P_graphdb,
      coalesce(topic.non_graphdb_like_count, 1.0) / 2951.0 as P_non_graphdb

x

    :::text
     topic.name                           | P_graphdb            | P_non_graphdb          
    --------------------------------------+----------------------+------------------------
     Neo4j                                | 0.38333333333333336  | 0.0013554727211114877  
     Graph Databases                      | 0.44583333333333336  | 0.0010166045408336157  
     NoSQL                                | 0.5666666666666667   | 0.04778041341917994    
     Big Data                             | 0.65                 | 0.08336157234835649    
     mongoDB                              | 0.20416666666666666  | 0.01626567265333785    
     Java Programming                     | 0.020833333333333332 | 0.003388681802778719   
     Java                                 | 0.20833333333333334  | 0.02507624534056252    
     Open Source                          | 0.5125               | 0.14977973568281938    
     Software Developers                  | 0.43333333333333335  | 0.12978651304642494    
     Data Visualization                   | 0.225                | 0.03422568620806506    
     Game Programming                     | 0.008333333333333333 | 0.0016943409013893595  
     Game Design                          | 0.0125               | 0.003049813622500847   
     Independent Game Development         | 0.008333333333333333 | 0.0010166045408336157  
     Indie Games                          | 0.008333333333333333 | 0.00033886818027787193 
     Video Game Development               | 0.008333333333333333 | 0.00033886818027787193 
     Mobile Game Development              | 0.008333333333333333 | 0.0006777363605557439  
     Mobile and Handheld game development | 0.008333333333333333 | 0.00033886818027787193 
     Video Game Design                    | 0.008333333333333333 | 0.0006777363605557439  
     Game Development                     | 0.008333333333333333 | 0.005083022704168078   
     Data Analytics                       | 0.4791666666666667   | 0.04879701796001355    
     Data Mining                          | 0.1875               | 0.03151474076584209    
     Data Science                         | 0.3                  | 0.03761436801084378    
    (22 rows)

x

    :::cypher
    # Single member classification
    match
      (member:Member { name : 'Rik Van Bruggen' })-[:LIKES]->(topic:Topic)
    with
      member,
      collect(coalesce(topic.graphdb_like_count, 1.0)) as graphdb_likes,
      collect(coalesce(topic.non_graphdb_like_count, 1.0)) as non_graphdb_likes
    with
      member,
      reduce(prod = 1.0, cnt in graphdb_likes | prod * (cnt / 240.0)) as P_graphdb,
      reduce(prod = 1.0, cnt in non_graphdb_likes | prod * (cnt / 2951.0)) as P_non_graphdb
    return
      member.name, P_graphdb > P_non_graphdb

x

    :::text
     member.name     | P_graphdb > P_non_graphdb 
    -----------------+---------------------------
     Rik Van Bruggen | True                      
    (1 row)

x

    :::cypher
    # How many graph db persons
    match
      (member:Member)-[:LIKES]->(topic:Topic),
      (graphdb:Group { name:'Graph Database - Amsterdam'})
    where
      not member-[:HAS_MEMBERSHIP]->graphdb
    with
      member,
      collect(coalesce(topic.graphdb_like_count, 1.0)) as graphdb_likes,
      collect(coalesce(topic.non_graphdb_like_count, 1.0)) as non_graphdb_likes
    with
      member,
      reduce(prod = 1.0, cnt in graphdb_likes | prod * (cnt / 240.0)) as P_graphdb,
      reduce(prod = 1.0, cnt in non_graphdb_likes | prod * (cnt / 2951.0)) as P_non_graphdb
    with
      P_graphdb > P_non_graphdb as graphdb_person
    return
      graphdb_person, count(*)

x

    :::text
     graphdb_person | count(*) 
    ----------------+----------
     False          | 1736     
     True           | 799      
    (2 rows)

x

    :::cypher
    # Co-occurrence based collaborative filtering on members
    match
      (us:Group { name: 'Graph Database - Amsterdam'})<-[:HAS_MEMBERSHIP]-(member:Member)-[:HAS_MEMBERSHIP]-(other:Group)
    with
      other, count(distinct member) as coo
    match
      other<-[:HAS_MEMBERSHIP]-(person:Member)
    return
      other.name as nm, coo, (coo * 1.0) / count(distinct person) as rank
    order by rank desc

x

    :::text
     nm                                                  | coo | rank                  
    -----------------------------------------------------+-----+-----------------------
     Netherlands Cassandra Users                         | 31  | 0.2540983606557377    
     The Amsterdam Applied Machine Learning Meetup Group | 55  | 0.20446096654275092   
     Open Web Meetup                                     | 4   | 0.10256410256410256   
     AmsterdamJS                                         | 35  | 0.06756756756756757   
     'Dam Runners                                        | 5   | 0.00946969696969697   
     Amsterdam Beer Meetup Group                         | 4   | 0.005934718100890208  
     Amsterdam Photo Club                                | 2   | 0.005235602094240838  
     Amsterdam Language Cafe                             | 2   | 0.0027662517289073307 
    (8 rows)

x

    :::cypher
    # Collaborative filtering with cosine similarity
    match
        (us:Group { name:'Graph Database - Amsterdam'})-[:ORGANISED]->(graph_meetup:Event)
        <-[:RSVP_ED]-(member:Member)-[:RSVP_ED]->(other_meetup:Event)
        <-[:ORGANISED]-(other:Group)
    where us <> other
    with
      us,
      other,
      member,
      count(distinct graph_meetup) as graph_rsvp,
      count(distinct other_meetup) as other_rsvp
    match
        us-[:ORGANISED]->(graph_meetup:Event),
        other-[:ORGANISED]->(other_meetup:Event)
    with
      us,
      other,
      member,
      (graph_rsvp * 1.0) / count(distinct graph_meetup) as graph_score,
      (other_rsvp * 1.0) / count(distinct other_meetup) as other_score
    with
      us,
      other,
      collect(graph_score * other_score) as score_product,
      collect(graph_score * graph_score) as graph_score_squared,
      collect(other_score * other_score) as other_score_squared,
      count(distinct member) as coo
    where coo > 1
    return
      us.name,
      other.name,
      coo,
      reduce(
        sum = 0,
        prd in score_product |
            sum + prd) / 
            ( sqrt( reduce(sum = 0, x in graph_score_squared | sum + x) ) * 
            sqrt( reduce(sum = 0, y in other_score_squared | sum + y) ) )
        as cosine_similarity
    order by cosine_similarity desc

x

    :::text
     us.name                    | other.name                                          | coo | cosine_similarity   
    ----------------------------+-----------------------------------------------------+-----+---------------------
     Graph Database - Amsterdam | The Amsterdam Applied Machine Learning Meetup Group | 38  | 0.7815846503441579  
     Graph Database - Amsterdam | Netherlands Cassandra Users                         | 16  | 0.6102571532587293  
     Graph Database - Amsterdam | AmsterdamJS                                         | 17  | 0.44444820784509104 
    (3 rows)
