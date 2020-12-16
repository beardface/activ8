const express = require('express');
const bodyParser= require('body-parser')
const app = express();

const MongoClient = require('mongodb').MongoClient

const connectionString = "mongodb://127.0.0.1:27017"
//const connectionString = "mongodb://192.168.1.37:27017"

// var faunadb = require('faunadb'), 
//     q = faunadb.query

// var faunaClient = new faunadb.Client({ secret: process.env.FAUNADB_API_KEY })

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

        // Enable FaunaDB
        // faunaClient.query(
        //     q.Map(
        //         q.Paginate(q.Match(q.Index('profiles_index'))),
        //         q.Lambda(x => q.Get(x))
        //   )
        // )
        // .then((all_profiles) => {
        //     faunaClient.query(
        //         q.Map(
        //             q.Paginate(q.Match(q.Index('all_devices_index'))),
        //             q.Lambda(x => q.Get(x))
        //     )
        //     )
        //     .then((all_devices) => {
        //         profiles = []
        //         all_profiles.data.forEach(element => {
        //             data = element.data
        //             data.ref = element.ref.id
        //             profiles.push(data)
        //         });

        //         devices = []
        //         console.log(all_devices)
        //         all_devices.data.forEach(element => {
        //             data = element.data
        //             data.ref = element.ref.id
        //             devices.push(data)
        //         });
    
        //         res.render('index.ejs', {
        //             profiles: profiles,
        //             devices: devices
        //         })
        //     })
        // })
        // .catch(e => {
        //     console.log(e)

        //     res.render('index.ejs', {
        //         profiles: [],
        //         devices: []
        //     })
        // })

        db.collection('profiles').find().toArray()
        .then(profiles => {
            db.collection('all_devices').find().toArray()
            .then(devices => {
                res.render('index.ejs', { 
                    profiles: profiles,
                    devices: devices
                })
            })
        })
        .catch(/* ... */)
    })

    app.get('/config', (req, res) => {
        //res.sendFile(__dirname + '/index.html')

        // Enable FaunaDB
        // faunaClient.query(q.Get(
        //     q.Ref(
        //         q.Collection('config'), '1'
        //     )
        // ))
        // .then((ret) => {
        //         // decrypt password for edit
        //         let buff = new Buffer(ret.data.twilio_sid, 'base64')
        //         ret.data.twilio_sid = buff.toString('ascii')
                
        //         // decrypt password for edit
        //         buff = new Buffer(ret.data.twilio_auth_token, 'base64')
        //         ret.data.twilio_auth_token = buff.toString('ascii')
                
        //         // decrypt password for edit
        //         buff = new Buffer(ret.data.router_password, 'base64')
        //         ret.data.router_password = buff.toString('ascii')

        //         res.render('config.ejs', { 
        //             config: ret.data,
        //         })
        //     }
        // )
        // .catch(e => {
        //         res.render('config.ejs', { 
        //             config: {},
        //         })
        //     }
        // )

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
            })
        })
        .catch(/* ... */)
    })
    
    app.post('/config_save', (req, res) => {
        var new_config = req.body
        new_config.router_password = Buffer.from(new_config.router_password).toString('base64')
        new_config.twilio_sid = Buffer.from(new_config.twilio_sid).toString('base64')
        new_config.twilio_auth_token = Buffer.from(new_config.twilio_auth_token).toString('base64')

        // Enable FaunaDB
        // faunaClient.query(q.Replace(
        //     q.Ref(q.Collection('config'), '1'),
        //     { data: new_config},
        // ))
        // .then((ret) => {
        //     console.log("Configuration updated!")
        //     console.log(ret)
        // })
        // .catch(
        //     faunaClient.query(q.Create(
        //         q.Ref(q.Collection('config'), '1'),
        //         { data: new_config},
        //     ))
        //     .then((ret) => {
        //         console.log("Configuration saved!")
        //         console.log(ret)
        //     })
        //     .catch((e) => console.log(e))
        // )

        const config = db.collection('config')
        config.replaceOne({}, new_config, {upsert: true})

        res.redirect('/')  
    })
    
    app.get('/profile_edit/:id', (req, res) => {

        // Enable FaunaDB
        // faunaClient.query(q.Get(
        //     q.Ref(
        //         q.Collection('profiles'), req.params.id)
        //     )
        // ).then((response) => {
        //     faunaClient.query(
        //         q.Map(
        //             q.Paginate(q.Match(q.Index('all_devices_index'))),
        //             q.Lambda(x => q.Get(x))
        //     )
        //     )
        //     .then((all_devices) => {
        //         devices = []
        //         console.log(all_devices)
        //         all_devices.data.forEach(element => {
        //             data = element.data
        //             data.ref = element.ref.id
        //             devices.push(data)
        //         });
    
        //         console.log(response)
                
        //         profile = response.data
        //         profile.ref = response.ref.id
    
        //         res.render('profile_edit.ejs', { 
        //             profile: profile,
        //             devices: devices
        //         })
        //     })
        // }).catch(e => {
        //     console.log(e)
        // })

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
                    devices: devices
                })
            })
        })
        .catch(/* ... */)
    })

    app.post('/profile_new', (req, res) => {
        // Enable FaunaDB
        // faunaClient.query(
        //     q.Create(
        //         q.Collection('profiles'),
        //         { data: { name: "new" }}
        //     )
        // ).then((ret) => {
        //     console.log(ret)
        //     res.redirect(req.get('referer'))
        // }).catch(e => {
        //     console.log(e)
        //     res.redirect(req.get('referer'))
        // })
        const config = db.collection('profiles')
        config.insertOne({
            name: "new",
            devices: [],
        })
        res.redirect('/')
    })

    app.post('/profile_save/:id', (req, res) => {
        var profile = req.body

        // Enable FaunaDB
        // faunaClient.query(
        //     q.Replace(
        //         q.Ref(q.Collection('profiles'), req.params.id),
        //         { data: profile}
        //     )
        // ).then((response) => {
        //     console.log(response)
        // }).catch(e => console.log(e))

        const profiles = db.collection('profiles')
        to_save = {
            "name": req.body.name,
            "google_calendar_id": req.body.google_calendar_id,
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
        profiles.replaceOne({name: req.params.id}, to_save, {upsert: true})

        res.redirect('/')
    })

    app.post('/profile_delete/:id', (req, res) => {
        // Enable FaunaDB
        // faunaClient.query(
        //     q.Delete(
        //         q.Ref(q.Collection('profiles'), req.params.id)
        //     )
        // ).then((response) => {
        //     console.log(response)
        // }).catch(e => console.log(e))

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
            })
        })
    })
  })
  .catch(error => console.error(error))
