# Tweeria Sources

Tweeria is a game with minimal user's involvement. Everytime you tweet, your alter ego finds adventures, kills monsters or gets items.

This is source code for Tweeria, you can use it and modify according the MIT licence.

Also there are two useful articles in our wiki we suggest to check: [configuration](https://github.com/idooo/tweeria/wiki/Configuration) and [Twitter API settings](https://github.com/idooo/tweeria/wiki/Twitter-API-settings) 

### Contribution

Tweeria is currently accepting contributions in the form of bug fixes or features (things that add new or improved functionality). Your pull requests will be reviewed and merged to master branch as soon as possible and deployed to the production [Tweeria website](http://tweeria.com). We really like to see new mechanics, integration with partners and content additions.

##### Legal
Commiting your code to this repository, submitting pull requests you are granting us permission to use the submitted change according to the terms of the project's license, and that the work being submitted is under appropriate copyright.

##### Important: you can use Tweeria source code in any way MIT license allows you, but you have no rights to use "Tweeria" trademark and you must clearly specify that your product is based on Tweeria Source Code 

### Install

#### 0. Introduction
Tweeria should work correctly on any linux/osx distributive. Originally Ubuntu LTS was used for production. This guide was written for Ubuntu 14.04.

Tweeria is a Python 2.7 application. We use memcache for caching, MongoDB as a database, SASS as a style preprocessor

In addition to this guide, you will need to create and register a Twitter Application using you Twitter account. Read more about this [here in our wiki](https://github.com/idooo/tweeria/wiki/Twitter-API-settings)

#### 1. Install necessary tools

Intstall packages using `apt-get`

```
sudo apt-get install python-pip python-dev build-essential git
```

#### 2. Thread safe version of Tweepy

Tweeria uses [Tweepy](https://github.com/tweepy/tweepy) library to parse user tweets, but unfortunately, this library is not thread safe so we monkey patched library, threw away some time-related stuff out and use [this custom build](https://github.com/idooo/tweepy-threadsafe)

You would need to do this to install:

```
git clone https://github.com/idooo/tweepy-threadsafe.git

cd tweepy-threadsafe/

sudo python setup.py install
```

#### 3. Image library

You need to install Python Image Library because Tweeria using it for thumbnail creation:

```
sudo apt-get install libjpeg62 libjpeg62-dev zlib1g-dev libfreetype6 libfreetype6-dev

sudo pip install pillow

sudo apt-get install python-imaging
```

#### 4. NodeJS and Ruby

Tweeria uses `grunt` to automate assets building process and SASS as a CSS preprocessor so you will need to install Node and Ruby

```
sudo apt-get install nodejs npm ruby

# For ubuntu you will require to create an alias for node like this 
# sudo ln -s /usr/bin/nodejs /usr/bin/node

sudo gem install sass
sudo npm install -g grunt-cli

* Make sure you pull the source before you execute this part *

cd tweeria
npm install

# run grunt to build assets
grunt
```

#### 5. Memcache (optional for caching)
Install memcache to enable caching

```
sudo apt-get install memcached
```

#### 6. MongoDB

Tweeria uses MongoDB as primary database to store all the things. You will need to install it and the best way to do it - read the officiall documentation and instructions [here](http://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/)

After the installation, you will need to create basic Tweeria collections with some data. There is a database backup in Tweeria sources, just unarchive it and use `mongorestore` tool (included in MongoDB package) 

```
cd tweeria/dbinit
tar xfv tweeriadb.tar.gz

mongorestore
```

You also will need to create Tweeria user with password in MongoDB. Run `mongo` command to connect to your database, change the current database (`use tweeria`) and execute this command

```
db.createUser(
    {
        user: "user",
        pwd: "password",
        roles:  [{ 
            role: "readWrite", db: "tweeria" 
        }]
    }
)
```


#### 7 Tweeria server:

Finally, we are ready to install Tweeria. First you must download the latest tweeria sources and install all the Python libraries it needs using `pip`

```
git clone https://github.com/idooo/tweeria.git
sudo pip install -r requirements.txt
```

Then you will need to create your own config file:

```
cd tweeria/conf
cp default.conf newconf.conf
```

Change there DB credentials, server settings and Twitter API keys. Please do not forget to change static files root directory `tools.staticdir.root` like `tools.staticdir.root = "/home/ido/tweeria"`

Read more about config settings [in our wiki](https://github.com/idooo/tweeria/wiki/Config)

Start Tweeria by executing `loader.sh <confname>` like this: `./loader.sh newconf`

Then you should see in your terminal something like this:

```
ido@ubuntu:~/tweeria$ ./loader.sh newconf
	Killing current web server
	Start server...
	Loading conf: newconf
	Server is up now! Cya!
ido@ubuntu:~/tweeria$ > Loading newconf config for Twitter
# ----------------------------------------- #
#  Tweeria version: 2.3.2b build: 2733
# ----------------------------------------- #
[27/Sep/2014:12:05:31] ENGINE Listening for SIGHUP.
[27/Sep/2014:12:05:31] ENGINE Listening for SIGTERM.
[27/Sep/2014:12:05:31] ENGINE Listening for SIGUSR1.
[27/Sep/2014:12:05:31] ENGINE Bus STARTING
[27/Sep/2014:12:05:31] ENGINE Started monitor thread '_TimeoutMonitor'.
[27/Sep/2014:12:05:31] ENGINE Serving on http://192.168.1.41:8080
[27/Sep/2014:12:05:31] ENGINE Bus STARTED
```

Open url in your browser (in my case it is [http://192.168.1.41:8080](localhost))

#### 8. Parser

To run parser you will need to execute `service_catcher.py <confname>` from the root Tweeria directory like this:

```
./service_catcher.py newconf
```

----------------
### Tools

There are couple scripts included to the Tweeria package, you can find them in `tools` directory 

#### _admin.py - Add admin rights

```
./_admin.py <conf> -s <username>
```
After this tou should see `Admin` link in the user menu popup like this:

![](http://shteinikov.com/files/tweeria/admin_link.png) 

#### converter.py - .csv to DB 

There are CSV file in `import_base` directory with all the static information Tweeria needs (default items, achievements, stats, dungeons and etc). If you would need to change this data in CSV files, you can use the convertor tools to update your database. Run `converter.py <conf> -h` to get all the possible options like this

```
./converter.py newconf -h
```


# License

##### The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

