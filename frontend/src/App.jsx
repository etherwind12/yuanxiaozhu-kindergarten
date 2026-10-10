import { Navigate, Route, Routes } from 'react-router-dom'

import MainLayout from './layouts/MainLayout'
import RequireAuth from './router/RequireAuth'
import RequirePerm from './router/RequirePerm'
import Login from './modules/auth/Login'
import ScanPage from './modules/scan/ScanPage'
import Dashboard from './modules/dashboard/Dashboard'
import Assets from './modules/assets/Assets'
import Borrow from './modules/borrow/Borrow'
import Inventory from './modules/inventory/Inventory'
import Inspection from './modules/inspection/Inspection'
import Teaching from './modules/teaching/Teaching'
import Report from './modules/report/Report'
import System from './modules/system/System'

import { DictProvider } from './store/dict'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/s/:token" element={<ScanPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <DictProvider>
              <MainLayout />
            </DictProvider>
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="assets" element={<Assets />} />
        <Route path="borrow" element={<Borrow />} />
        <Route
          path="inventory"
          element={
            <RequirePerm perm="inventory">
              <Inventory />
            </RequirePerm>
          }
        />
        <Route
          path="inspection"
          element={
            <RequirePerm perm="inspection">
              <Inspection />
            </RequirePerm>
          }
        />
        <Route
          path="teaching"
          element={
            <RequirePerm perm="reserve:apply">
              <Teaching />
            </RequirePerm>
          }
        />
        <Route path="report" element={<Report />} />
        <Route
          path="system"
          element={
            <RequirePerm perm="user:manage">
              <System />
            </RequirePerm>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
