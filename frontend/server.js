const express = require('express');
const bodyParser= require('body-parser')
const app = express();
const MongoClient = require('mongodb').MongoClient

var moment = require('moment');
//const connectionString = "mongodb://"+process.env.MONGO_HOST+":27017"
const connectionString = "mongodb://192.168.1.17:27017"

var ObjectID            = require('mongodb').ObjectID;

function getWeekDay(){
    today = new Date();
    //Create an array containing each day, starting with Sunday.
    var weekdays = new Array(
        "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    );
    //Use the getDay() method to get the day.
    var day = today.getDay();
    //Return the element that corresponds to that index.
    return weekdays[day];
}

MongoClient.connect(connectionString, {
    useUnifiedTopology: true
  })
  .then(client => {
    const db = client.db('activ8')

    app.set('view engine', 'ejs')
    app.use(bodyParser.urlencoded({ extended: true }))
    
    app.listen(process.env.PORT, function() {
        console.log('listening on '+process.env.PORT)
    })
    
    app.get('/', (req, res) => {

        db.collection('profiles').find().toArray()
        .then(profiles => {
            db.collection('all_devices').find().toArray()
            .then(devices => {
                db.collection('disabled_devices').find().toArray()
                .then(disabled => {
                    db.collection('events').find().toArray()
                    .then(events => {
                        disabled.forEach(device => {
                            profiles.forEach(profile => {
                                if(device.name == profile.name) {
                                    profile.disabled = true
                                }
                            })
                        })

                        events.forEach(event => {
                            console.log(event)

                            var name_of_day = getWeekDay();

                            var today = new Date();
                            var start = new Date('1/1/2020 '+event.start_time).getTime()
                            var end = new Date('1/1/2020 '+event.end_time).getTime()
                            var now = new Date('1/1/2020 '+today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds()).getTime()

                            if((event.days.indexOf(name_of_day) > -1) && now > start && now < end) {
                                profiles.forEach(profile => {
                                    if(event.user == profile.name) {
                                        if(!profile.active_events) {
                                            profile.active_events = [event]       
                                        } else {
                                            profile.active_events.push(event)
                                        }
                                    }
                                })
                            } else {
                                profiles.forEach(profile => {
                                    if(event.user == profile.name) {
                                        if(!profile.upcoming_events) {
                                            profile.upcoming_events = [event]       
                                        } else {
                                            profile.upcoming_events.push(event)
                                        }
                                    }
                                })
                            }
                        })

                        res.render('index.ejs', { 
                            profiles: profiles,
                            devices: devices,
                            disabled_devices: disabled,
                            moment: moment,
                        })
                    })
                })
            })
        })
        .catch(/* ... */)
    })

    app.get('/config', (req, res) => {
        db.collection('config').findOne({})
        .then(config => {
            if(config && config.twilio_sid) {
                // decrypt password for edit
                let buff = new Buffer(config.twilio_sid.toString('ascii'), 'base64')
                config.twilio_sid = buff.toString('ascii')
            }
            
            if(config && config.twilio_auth_token) {
            // decrypt password for edit
                buff = new Buffer(config.twilio_auth_token.toString('ascii'), 'base64')
                config.twilio_auth_token = buff.toString('ascii')
            }
            
            if(config && config.router_password) {
            // decrypt password for edit
                buff = new Buffer(config.router_password.toString('ascii'), 'base64')
                config.router_password = buff.toString('ascii')
            }

            res.render('config.ejs', { 
                config: config,
                moment: moment,
            })
        })
        .catch(/* ... */)
    })
    
    app.post('/config_save', (req, res) => {
        var new_config = req.body
        new_config.router_password = Buffer.from(new_config.router_password).toString('base64')
        new_config.twilio_sid = Buffer.from(new_config.twilio_sid).toString('base64')
        new_config.twilio_auth_token = Buffer.from(new_config.twilio_auth_token).toString('base64')

        const config = db.collection('config')
        config.updateOne({}, { "$set": new_config})

        res.redirect('/')  
    })
    
    app.get('/profile_edit/:id', (req, res) => {
        db.collection('profiles').findOne({name: req.params.id})
        .then(profile => {
            db.collection('all_devices').find().toArray()
            .then(devices => {
                if(profile.garmin_password){
                    // decrypt password for edit
                    let buff = new Buffer(profile.garmin_password.toString('ascii'), 'base64')
                    profile.garmin_password = buff.toString('ascii')
                }
    
                devices.forEach(d => {       
                    profile.devices.forEach(pd => {
                        if (d.mac == pd) {
                            d.checked = true
                        }
                    })
                });

                res.render('profile_edit.ejs', { 
                    profile: profile,
                    devices: devices,
                    moment: moment,
                })
            })
        })
        .catch(/* ... */)
    })

    app.post('/profile_new', (req, res) => {
        const config = db.collection('profiles')
        config.insertOne({
            name: "new",
            devices: [],
        })
        res.redirect('/')
    })

    app.post('/profile_save/:id', (req, res) => {
        var profile = req.body

        const profiles = db.collection('profiles')
        to_save = {
            "name": req.body.name,
            "image": req.body.image,
            "notify_phone_number": req.body.notify_phone_number,
            "garmin_username": req.body.garmin_username,
            "devices": [],
        }

        Object.keys(req.body).forEach(function(key){
            if(req.body[key] == 'on') {
                to_save.devices.push(key)
            }
        })

        to_save.garmin_password = Buffer.from(req.body.garmin_password).toString('base64')
        profiles.updateOne({name: req.params.id}, {"$set": to_save}, {upsert: true})

        res.redirect('/')
    })

    app.post('/profile_delete/:id', (req, res) => {
        const config = db.collection('profiles')
        config.deleteOne({
            name: req.params.id
        })

        res.redirect('/')
    })
    
    app.get('/logs', (req, res) => {
        const logs = db.collection('logs')
        logs.find().limit(100).sort({$natural:1}).toArray().then(result => {
            res.render('debug.ejs', { 
                logs: result,
                moment: moment,
            })
        })
    })

    app.post('/force_refresh', (req, res) => {
        const config = db.collection('config')
        config.updateOne({}, {"$set": {
            "next_update_time": new Date('2000-01-22T14:56:59.301Z')
        }})

        res.redirect('/')
    })
    
    app.get('/event_edit/:id', (req, res) => {
        db.collection('events').findOne({_id: new ObjectID(req.params.id)})
        .then(events => {
            console.log(events)

            res.render('event.ejs', { 
                event: events,
                moment: moment,
            })
        })
        .catch(/* ... */)
    })

    app.post('/event_save/:id', (req, res) => {
        var event = req.body

        to_save = {
            title: event.title,
            start_time: event.start_time,
            end_time: event.end_time,
            value: event.value,
            activity: event.activity,
            days: []
        }

        if(event['day_sunday'] == 'on'){
            to_save.days.push('Sunday')
        }
        if(event['day_monday'] == 'on'){
            to_save.days.push('Monday')
        }
        if(event['day_tuesday'] == 'on'){
            to_save.days.push('Tuesday')
        }
        if(event['day_wednesday'] == 'on'){
            to_save.days.push('Wednesday')
        }
        if(event['day_thursday'] == 'on'){
            to_save.days.push('Thursday')
        }
        if(event['day_friday'] == 'on'){
            to_save.days.push('Friday')
        }
        if(event['day_saturday'] == 'on'){
            to_save.days.push('Saturday')
        }

        db.collection('events').updateOne({_id: new ObjectID(req.params.id)}, {"$set": to_save}, {upsert: true})
        
        res.redirect('/')
    })
    
    app.post('/event_new/:name', (req, res) => {
        const config = db.collection('events')
        config.insertOne({
            user: req.params.name,
            days: [],
            title: '',
            start_time: '00:00:00',
            end_time: '00:00:00',
            activity: 'STEPS',
            value: 0
        })

        res.redirect('/')
    })

    app.post('/event_delete/:id', (req, res) => {
        const config = db.collection('events')
        config.deleteOne({
            _id: new ObjectID(req.params.id)
        })

        res.redirect('/')
    })
  })
  .catch(error => console.error(error))
