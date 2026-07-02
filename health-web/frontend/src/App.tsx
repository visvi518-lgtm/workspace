import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import Layout from '@/components/layout/Layout';
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import HealthBoardPage from '@/pages/HealthBoardPage';
import PostDetailPage from '@/pages/PostDetailPage';
import PostWritePage from '@/pages/PostWritePage';
import HealthManagementPage from '@/pages/HealthManagementPage';
import FreeBoardPage from '@/pages/FreeBoardPage';
import MyPage from '@/pages/MyPage';
import HealthChatPage from '@/pages/HealthChatPage';
import RecommendationPage from '@/pages/RecommendationPage';
import AdminPage from '@/pages/AdminPage';
import OAuthCallbackPage from '@/pages/OAuthCallbackPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user?.is_admin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* Public */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/callback" element={<OAuthCallbackPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/board/:boardType" element={<HealthBoardPage />} />
        <Route path="/board/:boardType/:id" element={<PostDetailPage />} />

        {/* Auth required */}
        <Route
          path="/board/:boardType/write"
          element={
            <RequireAuth>
              <PostWritePage />
            </RequireAuth>
          }
        />
        <Route
          path="/health"
          element={
            <RequireAuth>
              <HealthManagementPage />
            </RequireAuth>
          }
        />
        <Route
          path="/free-board"
          element={
            <RequireAuth>
              <FreeBoardPage />
            </RequireAuth>
          }
        />
        <Route
          path="/my-page"
          element={
            <RequireAuth>
              <MyPage />
            </RequireAuth>
          }
        />
        <Route
          path="/recommendation"
          element={
            <RequireAuth>
              <RecommendationPage />
            </RequireAuth>
          }
        />
        <Route
          path="/chat"
          element={
            <RequireAuth>
              <HealthChatPage />
            </RequireAuth>
          }
        />

        {/* Admin */}
        <Route
          path="/admin"
          element={
            <RequireAuth>
              <RequireAdmin>
                <AdminPage />
              </RequireAdmin>
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
