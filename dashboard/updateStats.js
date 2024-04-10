/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const STATS_API_URL =  "http://pdang-api.eastus.cloudapp.azure.com:8100/stats"
const EVENTS_URL = {
    switch_report: "http://pdang-api.eastus.cloudapp.azure.com:8110/switch_report", 
    configuration_file: "http://pdang-api.eastus.cloudapp.azure.com:8110/configuration_file" 
}

const CODE_LOG_URL = "http://pdang-api.eastus.cloudapp.azure.com:8120/events_stats"

// This function fetches and updates the general statistics
const getStats = (statsUrl) => {
    fetch(statsUrl)
        .then(res => res.json())
        .then((result) => {
            console.log("Received stats", result)
            updateStatsHTML(result);
        }).catch((error) => {
            updateStatsHTML(error.message, error = true)
            console.log("ERROR!!!!")
        })
}

// This function fetches a single event from the audit service
const getEvent = (eventType) => {
    const eventIndex = Math.floor(Math.random() * 100)

    fetch(`${EVENTS_URL[eventType]}?index=${eventIndex}`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`Error: status code ${res.status}`)
            }
            return res.json()
        })
        .then((result) => {
            console.log("Received event", result)
            updateEventHTML({...result, index: eventIndex}, eventType)
        }).catch((error) => {
            updateEventHTML({error: error.message, index: eventIndex}, eventType, error = true)
        })
}

// This function updates a single "event box"
const updateEventHTML = (data, eventType, error = false) => {
    const { index, ...values } = data
    const elem = document.getElementById(`event-${eventType}`)
    elem.innerHTML = `<h5>Event ${index}</h5>`
    
    // for error messages
    if (error === true) {
        const errorMsg = document.createElement("code")
        errorMsg.innerHTML = values.error
        elem.appendChild(errorMsg)
        return
    }

    // loops through the object and displays it in the DOM
    Object.entries(values).map(
        ([key, value]) => {
            const labelElm = document.createElement("span")
            const valueElm = document.createElement("span")
            labelElm.innerText = key
            valueElm.innerText = value
            const pElm = document.createElement("p")
            pElm.style.display = "flex"
            pElm.style.flexDirection = "column"
            pElm.appendChild(labelElm)
            pElm.appendChild(valueElm)
            elem.appendChild(pElm)
        }
    )

}

// This function updates the main statistics div
const updateStatsHTML = (data, error = false) => {
    const elem = document.getElementById("stats")
    if (error === true) {
        elem.innerHTML = `<code>${data}</code>`
        return
    }
    elem.innerHTML = ""
    Object.entries(data).map(([key, value]) => {
        const pElm = document.createElement("p")
        pElm.innerHTML = `<strong>${key}:</strong> ${value}`
        elem.appendChild(pElm)
    })
}

const setup = () => {
    const interval = setInterval(() => {
        getStats(STATS_API_URL)
        getStats(CODE_LOG_URL)
        getEvent("switch_report")
        getEvent("configuration_file")
    }, 5000); // Update every 5 seconds

    // initial call
    getStats(STATS_API_URL)
    getEvent("switch_report") 
    getEvent("configuration_file")
    // clearInterval(interval);
}

document.addEventListener('DOMContentLoaded', setup)