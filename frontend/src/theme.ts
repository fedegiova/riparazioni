import { createTheme } from '@mui/material/styles'

// Single place for app-wide Material theming. MUI defaults for now (no brand
// assets in the repo yet); adjust palette/typography here to rebrand.
const theme = createTheme({
  palette: {
    mode: 'light',
  },
})

export default theme
