const express = require('express');
const bodyParser= require('body-parser')
const app = express();

const MongoClient = require('mongodb').MongoClient

//const connectionString = "mongodb://127.0.0.1:27017"
const connectionString = "mongodb://192.168.1.37:27017"

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
        const config = db.collection('config')
        var new_config = req.body
        new_config.router_password = Buffer.from(new_config.router_password).toString('base64')
        new_config.twilio_sid = Buffer.from(new_config.twilio_sid).toString('base64')
        new_config.twilio_auth_token = Buffer.from(new_config.twilio_auth_token).toString('base64')
        config.replaceOne({}, new_config, {upsert: true})
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
    
    app.post('/profile_new', (req, res) => {
        const config = db.collection('profiles')
        config.insertOne({
            name: "new"
        })
        res.redirect(req.get('referer'))
    })

    app.post('/profile_save/:name', (req, res) => {
        const profiles = db.collection('profiles')
        var profile = req.body

        profile.garmin_password = Buffer.from(profile.garmin_password).toString('base64')
        profiles.replaceOne({name: req.params.name}, profile, {upsert: true})

        res.redirect(req.get('referer'))
    })

    app.post('/profile_delete/:name', (req, res) => {
        console.log(req.body)
        console.log(req.params.name)
    })
  })
  .catch(error => console.error(error))
