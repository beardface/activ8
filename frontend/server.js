const express = require('express');
const bodyParser= require('body-parser')
const app = express();

const MongoClient = require('mongodb').MongoClient

const connectionString = "mongodb://127.0.0.1:27017"

MongoClient.connect(connectionString, {
    useUnifiedTopology: true
  })
  .then(client => {
    const db = client.db('2FAt')

    app.set('view engine', 'ejs')
    app.use(bodyParser.urlencoded({ extended: true }))
    
    app.listen(3000, function() {
        console.log('listening on 3000')
    })
    
    app.get('/config', (req, res) => {
        //res.sendFile(__dirname + '/index.html')
        
        db.collection('config').findOne({})
        .then(config => {
            res.render('config.ejs', { 
                config: config,
            })
        })
        .catch(/* ... */)
    })
    
    app.post('/config_save', (req, res) => {
        // const garminAccount = db.collection('garmin_account')
        // var account = req.body
        // account.password = Buffer.from(account.password).toString('base64')
        // garminAccount.findOneAndReplace({}, account)
        console.log(req.body)
    })
    
    app.get('/profile', (req, res) => {
        db.collection('profiles').find().toArray()
        .then(profiles => {
            console.log(profiles)
            res.render('profile.ejs', { 
                profiles: profiles,
            })
        })
        .catch(/* ... */)
    })
    
    app.post('/profile_save', (req, res) => {
        console.log(req.body)
    })
  })
  .catch(error => console.error(error))
