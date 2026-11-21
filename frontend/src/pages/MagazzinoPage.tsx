import { useState } from 'react'
import { Box, Tab, Tabs, Typography } from '@mui/material'
import CylindersManager from '../components/CylindersManager'
import PartsManager from '../components/PartsManager'

function MagazzinoPage() {
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Magazzino
      </Typography>
      <Tabs
        value={tab}
        onChange={(_, value: number) => setTab(value)}
        aria-label="Magazzino sections"
      >
        <Tab label="Ricambi" />
        <Tab label="Ricambi Frigo" />
        <Tab label="Bombole" />
      </Tabs>
      <Box sx={{ mt: 2 }}>
        {tab === 0 && <PartsManager isRefrigeratorPart={false} />}
        {tab === 1 && <PartsManager isRefrigeratorPart />}
        {tab === 2 && <CylindersManager />}
      </Box>
    </Box>
  )
}

export default MagazzinoPage
