import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Layout,
  Menu,
  Typography,
  Spin,
  Space,
  Button,
  Drawer,
} from 'antd'
import { useQuery } from '@tanstack/react-query'
import type { MenuProps } from 'antd'
import * as Icons from '@ant-design/icons'
import { systemApi, type NavItem } from '@/api'
import { useResponsive } from '@/hooks/useResponsive'

const { Header, Sider, Content } = Layout
const { Title, Text } = Typography

/** 将 icon 字符串（如 "UserOutlined"）映射到 @ant-design/icons 组件 */
function resolveIcon(name: string): React.ReactNode {
  if (!name) return null
  const Comp = (Icons as unknown as Record<string, React.ComponentType>)[name]
  return Comp ? <Comp /> : null
}

/** 将后端 NavItem 数组转为 Ant Design Menu items */
function buildMenuItems(nav: NavItem[]): MenuProps['items'] {
  return nav.map((item) => ({
    key: item.path || item.key,
    icon: resolveIcon(item.icon),
    label: item.label,
    children: item.children?.length
      ? item.children.map((child) => ({
          key: child.path || child.key,
          icon: resolveIcon(child.icon),
          label: child.label,
        }))
      : undefined,
  }))
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { isMobile, isTablet } = useResponsive()

  // 移动端默认折叠侧边栏
  useEffect(() => {
    if (isMobile) setCollapsed(true)
  }, [isMobile])

  // 从后端动态获取插件注册的导航项
  const { data: navItems = [], isLoading: navLoading } = useQuery({
    queryKey: ['navigation'],
    queryFn: () =>
      systemApi.navigation().then((r) => r.data.navigation),
  })

  // 获取框架健康信息（应用名、版本）
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => systemApi.health().then((r) => r.data),
    refetchInterval: 60_000,
    retry: 2,
  })

  // 静态首项：仪表盘 + 健康检查（health 插件未注册导航，这里手动补充）
  const staticItems: MenuProps['items'] = [
    { key: '/dashboard', icon: <Icons.DashboardOutlined />, label: '仪表盘' },
    { key: '/health', icon: <Icons.HeartOutlined />, label: '健康检查' },
  ]

  // 合并静态项与后端动态导航项
  const allItems: MenuProps['items'] = [
    ...staticItems,
    ...(buildMenuItems(navItems) ?? []),
  ]

  // 自动展开当前路径所属的子菜单
  const openKeys = navItems
    .filter(
      (item) =>
        item.children?.some((c) => location.pathname.startsWith(c.path || '')) ||
        (item.path && location.pathname.startsWith(item.path)),
    )
    .map((item) => item.path || item.key)

  const onMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key)
    if (isMobile) setDrawerVisible(false)
  }

  // 侧边栏菜单内容（Sider / Drawer 共用）
  const MenuContent = () => (
    <>
      <div style={{ padding: isMobile ? 12 : 16, textAlign: 'center' }}>
        <Title level={isMobile ? 5 : 4} style={{ color: '#fff', margin: 0 }}>
          {healthData?.app || 'pywt'}
        </Title>
        {(!collapsed || isMobile) && (
          <Text style={{ color: 'rgba(255,255,255,0.45)', fontSize: isMobile ? 10 : 12 }}>
            FastAPI 插件模板
          </Text>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {navLoading ? (
          <Spin style={{ display: 'block', margin: '40px auto' }} />
        ) : (
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            defaultOpenKeys={openKeys}
            items={allItems}
            onClick={onMenuClick}
          />
        )}
      </div>

      <div
        style={{
          padding: isMobile ? 12 : 16,
          textAlign: 'center',
          borderTop: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Text style={{ color: 'rgba(255,255,255,0.45)', fontSize: isMobile ? 10 : 11 }}>
          v{healthData?.version || '加载中...'}
        </Text>
      </div>
    </>
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 移动端：Drawer；桌面端：Sider */}
      {isMobile ? (
        <Drawer
          placement="left"
          open={drawerVisible}
          onClose={() => setDrawerVisible(false)}
          width={220}
          styles={{ body: { background: '#001529', padding: 0 } }}
          closable={false}
        >
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <MenuContent />
          </div>
        </Drawer>
      ) : (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="dark"
          width={isTablet ? 180 : 220}
          collapsedWidth={isTablet ? 60 : 80}
        >
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <MenuContent />
          </div>
        </Sider>
      )}

      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: isMobile ? '0 12px' : '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            height: isMobile ? 44 : 48,
            lineHeight: isMobile ? '44px' : '48px',
          }}
        >
          <Space size="small">
            {isMobile && (
              <Button
                type="text"
                icon={<Icons.MenuOutlined style={{ fontSize: 18 }} />}
                onClick={() => setDrawerVisible(true)}
              />
            )}
            <Title level={5} style={{ margin: 0, fontSize: isMobile ? 14 : 16 }}>
              {isMobile ? healthData?.app || 'pywt' : `${healthData?.app || 'pywt'} · FastAPI 插件模板`}
            </Title>
          </Space>
          <Space size={isMobile ? 'small' : 'middle'}>
            <Icons.ApiOutlined />
            <Text style={{ fontSize: isMobile ? 12 : 14 }}>
              API {healthData?.version || '--'}
            </Text>
          </Space>
        </Header>

        <Content
          style={{
            padding: isMobile ? 12 : isTablet ? 16 : 24,
            background: '#f5f5f5',
            minHeight: 'calc(100vh - 48px)',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
