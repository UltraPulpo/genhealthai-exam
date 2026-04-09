import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
  user?: { first_name: string; last_name: string };
  onLogout?: () => void;
}

export default function PageLayout({
  children,
  title = 'GenHealth AI',
  user,
  onLogout,
}: PageLayoutProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          {user && (
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="body1">
                {user.first_name} {user.last_name}
              </Typography>
              {onLogout && (
                <Button color="inherit" onClick={onLogout}>
                  Logout
                </Button>
              )}
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Container component="main" sx={{ flex: 1, py: 3 }}>
        {children}
      </Container>
    </Box>
  );
}
