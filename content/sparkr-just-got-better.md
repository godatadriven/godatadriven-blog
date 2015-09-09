Title: SparkR just got better
Date: 2015-09-09 17:05
Slug: about-big-data
Author: Vincent D. Warmerdam
Excerpt: This document discusses some new features for SparkR that arrived as part of the 1.5 release of Spark. 
Template: article
Latex:

In this document I'll give a quick review of some exiting new features for SparkR from the new 1.5 version that had it's official release today. 

## Rstudio provisioned 

![](https://www.rstudio.com/wp-content/uploads/2014/06/RStudio-Ball.png)

Starting a full start SparkR service on aws just got a whole lot easier. It takes about 15 minutes and only requires you to do three simple things.

#### Step 1: Command line 

If you have your amazon `.pem` files in order on your machine as well as your aws credentials in your `.bash_profile` you can use the command line app in the `spark-ec2` folder to start up a cluster on amazon. 

From this folder, run this command;

```
./spark-ec2 \
  --key-pair=pems \
  --identity-file=/path/pems.pem \
  --region=eu-west-1 \
  -s 4 \
  --instance-type c3.xlarge \
  --copy-aws-credentials
  launch my-spark-cluster
```

This example will start a cluster with 4 slave nodes of type c3.xlarge in the eu-west-1 region. The name of the cluster is 'my-spark-cluster'. If you want a bigger cluster, you can set the preferences here. 

#### Step 2: Ssh + set password 

The same command line app allows you to ssh into the master machine of the spark cluster. 

```
./spark-ec2 -k pems-df -i /path/pems.pem --region=eu-west-1 login my-spark-cluster
```

Once you are logged in, you'll be logged in as the root user. For security reasons it is more preferable to have a seperate user for rstudio. This user has already been added to the system, the only thing you need to do is assign a password to it. 

```
passwd rstudio
```

#### Step 3: Login 

First, just check where the master server is located.

```
> curl icanhazip.com
```

Then fill in the link in your favorite browser and log in with the 'rstudio' user and the password that you've set. 

![](http://i.imgur.com/G6AbvPw.png)

You can use the `startSpark.R` script to quickly get started.  It creates a sparkContext and a sqlContext which you can then use to create distributed dataframes on your cluster. 

##### When you are done

If you are done with the cluster and saved all your files back to s3, you don't need to pay for the ec2 machines anymore. The cluster can then safely be destroyed via the same command line app as before. 

```
./spark-ec2 -k pems-df -i /path/pems.pem --region=eu-west-1 destroy my-spark-cluster
```

## Linear Models 

#### Regression Example 

```
ddf <- createDataFrame(sqlContext, ChickWeight)
ddf %>% 
  summary %>% 
  collect
```

###### Result 

```
  summary             weight               Time              Chick 
1   count                578                578                578 
2    mean 121.81833910034602 10.717993079584774 25.750865051903116 
3  stddev  71.01045205007217  6.752550828025898   14.5561866041844 
4     min               35.0                0.0                  1 
5     max              373.0               21.0                  9 
                Diet
1                578
2  2.235294117647059
3 1.1616716269489116
4                  1
5                  4
```

In this new SparkR shell you will notice that the `glm` method now comes from multiple packages. 

```
?glm
Help on topic ‘glm’ was found in the following packages:

  Package               Library
  SparkR                /Users/code/Downloads/spark-1.5.0-bin-hadoop2.6/R/lib
  stats                 /Library/Frameworks/R.framework/Versions/3.2/Resources/library
```

You can run the model and save it's parameters in a variable, just like in normal R. 

```
dist_mod <- glm(weight ~ Time + Diet, data = ddf, family = "gaussian")
```

To view the characteristics of the regression you'll only need to run it through the summary function (a pattern common for many things in R). 

```
dist_mod %>% summary
```

###### Result

```
$coefficients
              Estimate
(Intercept)  41.157845
Time          8.750492
Diet__1     -30.233456
Diet__2     -14.067382
Diet__3       6.265952
```

This model can be applied to new data to create predictions, very much in the same style as you would in normal R models/dataframes.

```
dist_mod %>% 
  predict(newData = ddf) %>% 
  showDF
```

###### Result 

```
+------+----+-----+----+------------------+-----+------------------+
|weight|Time|Chick|Diet|          features|label|        prediction|
+------+----+-----+----+------------------+-----+------------------+
|  42.0| 0.0|    1|   1|     (4,[1],[1.0])| 42.0|10.924388954283739|
|  51.0| 2.0|    1|   1| [2.0,1.0,0.0,0.0]| 51.0| 28.42537280265673|
|  59.0| 4.0|    1|   1| [4.0,1.0,0.0,0.0]| 59.0| 45.92635665102972|
|  64.0| 6.0|    1|   1| [6.0,1.0,0.0,0.0]| 64.0| 63.42734049940272|
|  76.0| 8.0|    1|   1| [8.0,1.0,0.0,0.0]| 76.0| 80.92832434777571|
|  93.0|10.0|    1|   1|[10.0,1.0,0.0,0.0]| 93.0| 98.42930819614871|
| 106.0|12.0|    1|   1|[12.0,1.0,0.0,0.0]|106.0|115.93029204452169|
| 125.0|14.0|    1|   1|[14.0,1.0,0.0,0.0]|125.0| 133.4312758928947|
| 149.0|16.0|    1|   1|[16.0,1.0,0.0,0.0]|149.0|150.93225974126767|
| 171.0|18.0|    1|   1|[18.0,1.0,0.0,0.0]|171.0|168.43324358964065|
| 199.0|20.0|    1|   1|[20.0,1.0,0.0,0.0]|199.0|185.93422743801366|
| 205.0|21.0|    1|   1|[21.0,1.0,0.0,0.0]|205.0|194.68471936220016|
|  40.0| 0.0|    2|   1|     (4,[1],[1.0])| 40.0|10.924388954283739|
|  49.0| 2.0|    2|   1| [2.0,1.0,0.0,0.0]| 49.0| 28.42537280265673|
|  58.0| 4.0|    2|   1| [4.0,1.0,0.0,0.0]| 58.0| 45.92635665102972|
|  72.0| 6.0|    2|   1| [6.0,1.0,0.0,0.0]| 72.0| 63.42734049940272|
|  84.0| 8.0|    2|   1| [8.0,1.0,0.0,0.0]| 84.0| 80.92832434777571|
| 103.0|10.0|    2|   1|[10.0,1.0,0.0,0.0]|103.0| 98.42930819614871|
| 122.0|12.0|    2|   1|[12.0,1.0,0.0,0.0]|122.0|115.93029204452169|
| 138.0|14.0|    2|   1|[14.0,1.0,0.0,0.0]|138.0| 133.4312758928947|
+------+----+-----+----+------------------+-----+------------------+
```

#### A small GOTYA 

You could compare the SparkR model results from the ChickWeight regression with the results from the normal R lm method. What you see might scare you a bit. 

```
df <- ChickWeight
loc_mod <- glm(weight ~ Time + Diet, data = df)
loc_mod %>% summary
```

###### Results 

```
Coefficients:
            Estimate Std. Error t value Pr(>|t|)    
(Intercept)  10.9244     3.3607   3.251  0.00122 ** 
Time          8.7505     0.2218  39.451  < 2e-16 ***
Diet2        16.1661     4.0858   3.957 8.56e-05 ***
Diet3        36.4994     4.0858   8.933  < 2e-16 ***
Diet4        30.2335     4.1075   7.361 6.39e-13 ***
```

Compare this output with the distributed glm output. You might be frightned slightly at this point. The two models give very different output! 

Don't be scared just yet. The way that Spark has implemented machine learning is different it is still doing proper regression. 

The main difference is that R-glm translates the `Diet1` variable to be the constant intercept whereas the SparkR-glm translates `Diet4`. The only different therefore is a linear transformation of the model and the prediction outcomes shoulds still be the same. Another way to confirm this is to notice that the different between `Diet2` and `Diet3` is the same in both models and the parameter for `Time` is also the same. 

```
loc_mod %>% predict(df) %>% head(20)
```

###### Result 

```
        1         2         3         4         5         6         7         8
 10.92439  28.42537  45.92636  63.42734  80.92833  98.42931 115.93029 133.43128
        9        10        11        12        13        14        15        16
150.93226 168.43324 185.93423 194.68472  10.92439  28.42537  45.92636  63.42734
       17        18        19        20
 80.92833  98.42931 115.93029 133.43128
```
#### Classification Example 

By turning the family parameter from "gaussian" to "binomial" we turn the linear regression into a logistic regression. 

```
df <- data.frame(a = c(1,1,1,0,0,0), b = c(6,7,8,1,2,3))
ddf <- createDataFrame(sqlContext, df)
mod <- glm(a ~ b, data=ddf, family="binomial")
mod %>% 
  predict(newData = ddf) %>% 
  showDF
```

###### Result 

```
+---+---+--------+-----+--------------------+--------------------+----------+
|  a|  b|features|label|       rawPrediction|         probability|prediction|
+---+---+--------+-----+--------------------+--------------------+----------+
|1.0|6.0|   [6.0]|  1.0|[-16.405749578003...|[7.50021053099107...|       1.0|
|1.0|7.0|   [7.0]|  1.0|[-27.201563029171...|[1.53642468901809...|       1.0|
|1.0|8.0|   [8.0]|  1.0|[-37.997376480340...|[3.14737918119432...|       1.0|
|0.0|1.0|   [1.0]|  0.0|[37.5733176778398...|[1.0,4.8096720602...|       0.0|
|0.0|2.0|   [2.0]|  0.0|[26.7775042266712...|[0.99999999999765...|       0.0|
|0.0|3.0|   [3.0]|  0.0|[15.9816907755026...|[0.99999988538542...|       0.0|
+---+---+--------+-----+--------------------+--------------------+----------+
```

The logistic version of glm unfortuntaly doesn't give us a nice summary output at the moment. This is a known [missing feature](https://issues.apache.org/jira/browse/SPARK-9836) and should become available as of Spark 1.6. Another problem is that SparkR currently does not seem to support strings; which means that all classification tasks need to be cast to integers manually. 

```
names(iris) <- c("sepal_length","sepal_width","petal_length","petal_width","species")

ddf <- sqlContext %>% 
  createDataFrame(iris) %>% 
  withColumn("to_pred", .$species == "setosa") 

glm(to_pred ~ sepal_length + sepal_width + petal_length + petal_width, family = "binomial", data = ddf) %>% 
  predict(newData = ddf) %>% 
  showDF
```
Note that Spark doesn't like points in column names, which is why they are manually reset here. 

###### Result

```
+-------+-------+-------+-------+-------+-------+ ... +----------+
|sep_len|sep_wid|pet_len|pet_wid|species|to_pred| ... |prediction|
+-------+-------+-------+-------+-------+-------+ ... +----------+
|    5.1|    3.5|     1.4|   0.2| setosa|   true| ... |       1.0|
|    4.9|    3.0|     1.4|   0.2| setosa|   true| ... |       1.0|
|    4.7|    3.2|     1.3|   0.2| setosa|   true| ... |       1.0|
|    4.6|    3.1|     1.5|   0.2| setosa|   true| ... |       1.0|
|    5.0|    3.6|     1.4|   0.2| setosa|   true| ... |       1.0|
|    5.4|    3.9|     1.7|   0.4| setosa|   true| ... |       1.0|
|    4.6|    3.4|     1.4|   0.3| setosa|   true| ... |       1.0|
|    5.0|    3.4|     1.5|   0.2| setosa|   true| ... |       1.0|
|    4.4|    2.9|     1.4|   0.2| setosa|   true| ... |       1.0|
|    4.9|    3.1|     1.5|   0.1| setosa|   true| ... |       1.0|
|    5.4|    3.7|     1.5|   0.2| setosa|   true| ... |       1.0|
|    4.8|    3.4|     1.6|   0.2| setosa|   true| ... |       1.0|
|    4.8|    3.0|     1.4|   0.1| setosa|   true| ... |       1.0|
|    4.3|    3.0|     1.1|   0.1| setosa|   true| ... |       1.0|
|    5.8|    4.0|     1.2|   0.2| setosa|   true| ... |       1.0|
|    5.7|    4.4|     1.5|   0.4| setosa|   true| ... |       1.0|
|    5.4|    3.9|     1.3|   0.4| setosa|   true| ... |       1.0|
|    5.1|    3.5|     1.4|   0.3| setosa|   true| ... |       1.0|
|    5.7|    3.8|     1.7|   0.3| setosa|   true| ... |       1.0|
|    5.1|    3.8|     1.5|   0.3| setosa|   true| ... |       1.0|
+-------+-------+-------+-------+-------+-------+ ... +----------+
only showing top 20 rows
```

### More Advanced Types and Queries 

A few nice features were added in Spark 1.5 in regards to types and operations in distributed data frames. 

#### The %in% operator 

This was definately missing in Spark 1.4 but now you can do more complex queries via the `%in%` operator. 

```
ddf <- createDataFrame(sqlContext, ChickWeight)
ddf %>% 
  filter(.$Diet %in% c("3","4")) %>% 
  sample(TRUE, 0.05) %>% 
  collect
```

###### Result 

```
   weight Time Chick Diet
1      87    6    35    3
2      48    2    37    3
3     109   10    38    3
4     232   18    38    3
5      66    4    40    3
6     215   16    40    3
7     155   12    41    4
8     204   16    42    4
9     198   18    43    4
10    101    8    46    4
```

#### Date types 

You can now start playing around with dates in SparkR.

```
df <- data.frame(
  date = as.Date("2015-04-01") + 0:99, 
  r = runif(100)
)

ddf <- createDataFrame(sqlContext, df) 
ddf %>% printSchema
```

###### Result 

```
root
 |-- date: date (nullable = true)
 |-- r: double (nullable = true)
```

You can filter these dates by using date types. 

```
ddf %>% 
  filter(.$date > as.Date("2015-04-03")) %>% 
  filter(.$date < as.Date("2015-04-08")) %>% 
  collect
```

###### Result 

```
        date         r
1 2015-04-04 0.5821896
2 2015-04-05 0.9939826
3 2015-04-06 0.4792869
4 2015-04-07 0.3411329
```

SparkR even has some lubridate-ish support for date manipulation.

```
ddf %>% 
  withColumn("dom", .$date %>% dayofmonth) %>% 
  withColumn("doy", .$date %>% dayofyear) %>% 
  withColumn("woy", .$date %>% weekofyear) %>% 
  head
```

###### Result

```
        date         r dom doy woy
1 2015-04-01 0.2736077   1  91  14
2 2015-04-02 0.2015249   2  92  14
3 2015-04-03 0.3586754   3  93  14
4 2015-04-04 0.6162447   4  94  14
5 2015-04-05 0.5220081   5  95  14
6 2015-04-06 0.4814839   6  96  15
```

You can do similar things with datetimes.

```
df <- data.frame(
  t = as.POSIXct("2015-01-01 00:00:00") + runif(1000)*10000, 
  r = runif(1000)
)

ddf <- createDataFrame(sqlContext, df) 
ddf %>% printSchema
```

###### Result 

```
root
 |-- t: timestamp (nullable = true)
 |-- r: double (nullable = true)
```

Besides dates, we've also got some lubri-time methods in SparkR now. 

```
ddf %>% 
  withColumn("hour", .$t %>% hour) %>% 
  withColumn("minute", .$t %>% minute) %>% 
  withColumn("unix_t", .$t %>% unix_timestamp) %>% 
  head
```

###### Result 

```
                    t         r hour minute     unix_t
1 2015-01-01 01:08:09 0.1484953    1      8 1420070889
2 2015-01-01 02:27:22 0.6907954    2     27 1420075642
3 2015-01-01 01:11:24 0.6616176    1     11 1420071084
4 2015-01-01 00:11:06 0.9897747    0     11 1420067466
5 2015-01-01 02:07:13 0.2923660    2      7 1420074433
6 2015-01-01 01:06:16 0.6781178    1      6 1420070776
```

For most dataframe operations, this is nice to start playing with, but don't expect the full flexibility of base R just yet. As of right now dates and dateimes cannot be summerized and they cannot be used in models. This is a current known issue in [Jira](https://issues.apache.org/jira/browse/SPARK-10520) that peolpe are working on. 

#### Levenshtein 

These might fall in the special usecase category, but it can be suprisingly handy when trying to find similar names in a large databank. 
```
df <- data.frame(
  a = c('saark', 'spork', 'siaru', 'soobk'), 
  b = c('spark', 'spark', 'spark', 'spark')
)

ddf <- createDataFrame(sqlContext, df) 
ddf$c <- levenshtein(ddf$a, ddf$b)
ddf %>% head
```

###### Results 

```
      a     b c
1 saark spark 1
2 spork spark 1
3 siaru spark 2
4 soobk spark 3
```

#### Regex 

Again, regexes are a bit of a special use case to a lot of R users but they are invaluable when analysing log files. 

```
df <- data.frame(
  s = c('100-202', '2a4ta24', '300-200', 't2t2t2')
)

ddf <- createDataFrame(sqlContext, df) 

ddf %>% 
  withColumn('regex1', regexp_extract(.$s, "(\\d+)-(\\d+)", 1)) %>% 
  withColumn('regex2', regexp_extract(.$s, "(\\d+)-(\\d+)", 2)) %>% 
  withColumn('regex3', regexp_replace(.$s, "(\\d+)-(\\d+)", "HERE!")) %>% 
  head

```

###### Results 

```
        s regex1 regex2  regex3
1 100-202    100    202   HERE!
2 2a4ta24               2a4ta24
3 300-200    300    200   HERE!
4  t2t2t2                t2t2t2
```

## The future 

Spark could use some more features, but the recent additions already grant many usecases. Spark is a project with enourmous traction and has a new release every 3 months, so you can expect more to come.

Being able to work with a distributed dataframe in a dplyr-like syntax really opens up doors for R users who want to handle larger datasets. The fact that all of this can run on amazon cheaply adds to the benefit. 