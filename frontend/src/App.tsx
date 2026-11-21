import { Box, CssBaseline } from '@mui/material'
import { ThemeProvider } from '@mui/material/styles'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import AnagraficaPage from './pages/AnagraficaPage'
import CylinderPage from './pages/CylinderPage'
import HomePage from './pages/HomePage'
import MagazzinoPage from './pages/MagazzinoPage'
import NotFoundPage from './pages/NotFoundPage'
import RepairPage from './pages/RepairPage'
import RepairsListPage from './pages/RepairsListPage'
import SettingsPage from './pages/SettingsPage'
import WorkLogPage from './pages/WorkLogPage'
import theme from './theme'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Box>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/repairs" element={<RepairsListPage />} />
              <Route path="/repairs/new" element={<RepairPage />} />
              <Route path="/repairs/:id" element={<RepairPage />} />
              <Route
                path="/repairs/:id/work-log/:entryId"
                element={<WorkLogPage />}
              />
              <Route path="/magazzino" element={<MagazzinoPage />} />
              <Route path="/magazzino/bombole/:id" element={<CylinderPage />} />
              <Route path="/anagrafica" element={<AnagraficaPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
