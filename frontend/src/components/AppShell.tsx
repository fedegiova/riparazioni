import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Breadcrumbs,
  IconButton,
  Link as MuiLink,
  Toolbar,
  Typography,
} from '@mui/material'
import HomeIcon from '@mui/icons-material/Home'
import Inventory2Icon from '@mui/icons-material/Inventory2'
import ListAltIcon from '@mui/icons-material/ListAlt'
import PeopleIcon from '@mui/icons-material/People'
import SettingsIcon from '@mui/icons-material/Settings'
import { Link as RouterLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

const EDITOR_ROUTE = /^\/repairs\/(new|\d+)(\/work-log\/(new|\d+))?$/

type Crumb = { label: string; to?: string }

function crumbsFor(pathname: string): Crumb[] {
  if (pathname === '/') return [{ label: 'Home' }]
  if (pathname === '/repairs') {
    return [{ label: 'Home', to: '/' }, { label: 'Repairs' }]
  }
  if (pathname === '/repairs/new') {
    return [
      { label: 'Home', to: '/' },
      { label: 'Repairs', to: '/repairs' },
      { label: 'New repair' },
    ]
  }
  const workLog = pathname.match(/^\/repairs\/(\d+)\/work-log\/(new|\d+)$/)
  if (workLog) {
    return [
      { label: 'Home', to: '/' },
      { label: 'Repairs', to: '/repairs' },
      { label: `Repair #${workLog[1]}`, to: `/repairs/${workLog[1]}` },
      { label: workLog[2] === 'new' ? 'New work log' : `Work log #${workLog[2]}` },
    ]
  }
  const repair = pathname.match(/^\/repairs\/(\d+)$/)
  if (repair) {
    return [
      { label: 'Home', to: '/' },
      { label: 'Repairs', to: '/repairs' },
      { label: `Repair #${repair[1]}` },
    ]
  }
  if (pathname === '/magazzino') {
    return [{ label: 'Home', to: '/' }, { label: 'Magazzino' }]
  }
  if (pathname === '/anagrafica') {
    return [{ label: 'Home', to: '/' }, { label: 'Anagrafica' }]
  }
  if (pathname === '/settings') {
    return [{ label: 'Home', to: '/' }, { label: 'Settings' }]
  }
  return [{ label: 'Home', to: '/' }]
}

function sectionFor(pathname: string): string {
  if (pathname.startsWith('/repairs')) return '/repairs'
  if (pathname.startsWith('/magazzino')) return '/magazzino'
  if (pathname.startsWith('/anagrafica')) return '/anagrafica'
  return ''
}

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const crumbs = crumbsFor(location.pathname)
  const isEditor = EDITOR_ROUTE.test(location.pathname)
  const section = sectionFor(location.pathname)

  return (
    <Box sx={{ minHeight: '100vh', pb: isEditor ? 0 : 8 }}>
      <AppBar position="sticky">
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            aria-label="Go to home"
            onClick={() => navigate('/')}
            sx={{ mr: 1 }}
          >
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" component="div">
            Riparazioni
          </Typography>
          <IconButton
            color="inherit"
            edge="end"
            aria-label="Settings"
            onClick={() => navigate('/settings')}
            sx={{ ml: 'auto' }}
          >
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box sx={{ px: 3, py: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Breadcrumbs aria-label="Breadcrumb">
          {crumbs.map((crumb, index) =>
            crumb.to && index < crumbs.length - 1 ? (
              <MuiLink
                key={crumb.label}
                component={RouterLink}
                to={crumb.to}
                underline="hover"
                color="inherit"
              >
                {crumb.label}
              </MuiLink>
            ) : (
              <Typography key={crumb.label} color="text.primary">
                {crumb.label}
              </Typography>
            ),
          )}
        </Breadcrumbs>
      </Box>

      <Box component="main" sx={{ p: 3 }}>
        <Outlet />
      </Box>

      {!isEditor && (
        <BottomNavigation
          showLabels
          value={section}
          onChange={(_event, value: string) => navigate(value)}
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            bgcolor: 'background.paper',
            borderTop: 1,
            borderColor: 'divider',
          }}
        >
          <BottomNavigationAction
            label="Repairs List"
            value="/repairs"
            icon={<ListAltIcon />}
          />
          <BottomNavigationAction
            label="Magazzino"
            value="/magazzino"
            icon={<Inventory2Icon />}
          />
          <BottomNavigationAction
            label="Anagrafica"
            value="/anagrafica"
            icon={<PeopleIcon />}
          />
        </BottomNavigation>
      )}
    </Box>
  )
}

export default AppShell
