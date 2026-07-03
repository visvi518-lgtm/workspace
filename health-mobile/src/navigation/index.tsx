import { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../services/api';

import LoginScreen from '../screens/auth/LoginScreen';
import HomeScreen from '../screens/HomeScreen';
import HealthScreen from '../screens/HealthScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function TabIcon({ emoji }: { emoji: string }) {
  return <Text style={{ fontSize: 20 }}>{emoji}</Text>;
}

function MainTabs() {
  const { logout } = useAuthStore();
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#fff' },
        headerTitleStyle: { fontWeight: '700', color: '#111827', fontSize: 17 },
        tabBarStyle: { borderTopColor: '#F3F4F6', backgroundColor: '#fff' },
        tabBarActiveTintColor: '#2563EB',
        tabBarInactiveTintColor: '#9CA3AF',
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: '모티AI',
          tabBarLabel: '홈',
          tabBarIcon: () => <TabIcon emoji="🏠" />,
          headerRight: () => (
            <Text
              onPress={logout}
              style={{ marginRight: 16, color: '#EF4444', fontSize: 14 }}
            >
              로그아웃
            </Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function Navigation() {
  const { isAuthenticated, loadToken, setAuth, logout } = useAuthStore();
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    const init = async () => {
      const token = await loadToken();
      if (token) {
        try {
          const res = await authApi.me();
          await setAuth(token, res.data);
        } catch {
          await logout();
        }
      }
      setInitializing(false);
    };
    init();
  }, []);

  if (initializing) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#2563EB" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {isAuthenticated ? (
            <>
              <Stack.Screen name="Main" component={MainTabs} />
              <Stack.Screen
                name="Health"
                component={HealthScreen}
                options={{ title: '건강 기록', headerBackTitle: '홈' }}
              />
            </>
          ) : (
            <Stack.Screen name="Login" component={LoginScreen} />
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
