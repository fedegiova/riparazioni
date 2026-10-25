import { Box, Typography } from '@mui/material'

function NotFoundPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1">
        404
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Page not found.
      </Typography>
    </Box>
  )
}

export default NotFoundPage
