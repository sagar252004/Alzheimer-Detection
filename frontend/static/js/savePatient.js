async function savePatient(){

    if(sessionStorage.getItem("saved")){
        alert("Patient already saved");
        return;
    }

    const patientData = {
        name: sessionStorage.getItem("name"),
        age: sessionStorage.getItem("age"),
        prediction: sessionStorage.getItem("prediction"),
        voice_file: sessionStorage.getItem("voice_file")
    };

    const response = await fetch("/save_patient",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body: JSON.stringify(patientData)
    });

    const data = await response.json();

    if(data.status==="success"){
        sessionStorage.setItem("saved",true);
    }

    alert(data.message);
}