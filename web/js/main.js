/*
 * Konkka
 */


// State manipulation


function State(name, users, bills) {

    const save = () => {
        throw "Not implemeted"
    }

    const load = () => {
        throw "Not implemeted"
    }

    const state = {
        name: name,
        users: users,
        bills: bills,
        save: save,
        load: load
    }

    return state

}


function calculateBalance() {

}


function calculateFlow() {

}


// App components


function createContainer(d) {
    let div = d.createElement("div")
    div.className = "Container"
    return div
}


function createMenu(d, cfg) {
    // TODO cfg contains item configs
    let menu = d.createElement("div")
    menu.className = "Menu"
    return menu
}
