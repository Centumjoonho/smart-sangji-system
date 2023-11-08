    /*
:안주영
*/


document.addEventListener("DOMContentLoaded", () => {
    setTimer();
    setDataCount();
});

setTimer = () => {
    const label = "현재 시간: ";
    const id = $('#header-top-info');
    const now = new Date();
    now.setHours(now.getHours() + 9);
    id.html(label + now.toISOString().replace('T', ' ').substring(0, 19));
    setTimeout(setTimer, 1000);
}

setDataCount = () => {
    const relatvie_url = '/getdatacount';
    $.ajax({
        url : relatvie_url,
        type : 'GET',
    })
    .done((res) => {
        if (typeof res == 'object'){
            const {kma_count, di_count, living_count} = res;
            $("#kma_count").html(kma_count);
            $("#di_count").html(di_count);
            $("#living_count").html(living_count);
        }
    })
    .fail((err) => console.log(err))
}
    
    