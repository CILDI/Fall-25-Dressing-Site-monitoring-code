import React, { useEffect, useState } from 'react'
import { supabase } from './supabaseClient'

function App() {
  const [latest, setLatest] = useState(null)

  async function fetchLatest() {
    const { data, error } = await supabase
      .from('photos')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1)

    if (error) {
      console.error(error)
      return
    }

    if (data.length === 0) {
      setLatest("none")
      return
    }

    const row = data[0]

    // === DETECT JSON PREDICTIONS ===
    const colorMap = {
      "Blood": "#ff4d4d",
      "Dressing": "#cfcfcf",
      "Red Skin": "#4da3ff",
      "Pus": "#66ff66",
      "Dressing Damage": "#000000",
      "Catheter": "#FFA500"
    }

    const keywords = Object.keys(colorMap)
    let detected = []

    if (row.result_json && row.result_json.predictions) {
      for (const pred of row.result_json.predictions) {
        if (keywords.includes(pred.class)) {
          detected.push(pred.class)
        }
      }
    }

    // === BACKGROUND STYLE ===
    if (detected.length === 1) {
      document.body.style.background = colorMap[detected[0]]
    } else if (detected.length > 1) {
      const colors = detected.map(d => colorMap[d])
      const step = 100 / colors.length
      let gradientStops = ""

      colors.forEach((color, i) => {
        const start = i * step
        gradientStops += `${color} ${start}%, ${color} ${start + step}%, `
      })

      gradientStops = gradientStops.slice(0, -2)

      document.body.style.background =
        `repeating-linear-gradient(45deg, ${gradientStops})`
      document.body.style.backgroundSize = "60px 60px"
    } else {
      document.body.style.background = "#f0f0f0"
    }

    setLatest({ row, detected, colorMap })
  }

  useEffect(() => {
    fetchLatest()

    // REALTIME SUBSCRIPTION
    const subscription = supabase
      .channel('photos-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'photos' },
        payload => {
          console.log("Realtime update detected:", payload);
          fetchLatest();
        }
      )
      .subscribe();

    return () => supabase.removeChannel(subscription)
  }, [])

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ fontSize: "1.6em" }}>Nurse APP</h1>

      {/* No data */}
      {latest === "none" && (
        <div style={card}>No data found</div>
      )}

      {/* Loading */}
      {!latest && latest !== "none" && (
        <div style={card}>Loading...</div>
      )}

      {/* Data Found */}
      {latest && latest !== "none" && (
        <div style={card}>
          <h2 style={{ marginTop: 0 }}>Detected:</h2>

          {latest.detected.length === 0 && (
            <p>None</p>
          )}

          {latest.detected.map(det => (
            <div
              key={det}
              style={{
                color: latest.colorMap[det],
                fontWeight: "bold",
                fontSize: "20px",
                marginBottom: "5px"
              }}
            >
              {det}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const card = {
  background: "#fff",
  padding: "15px 20px",
  margin: "10px 0",
  borderRadius: "8px",
  boxShadow: "0 2px 5px rgba(0,0,0,0.1)"
}

export default App
