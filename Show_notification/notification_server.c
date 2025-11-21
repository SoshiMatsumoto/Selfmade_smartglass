#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <glib.h>
#include <gio/gio.h>

/* UUIDs */
#define SERVICE_UUID "12345678-1234-5678-1234-56789abcdef0"
#define CHAR_UUID    "12345678-1234-5678-1234-56789abcdef1"

/* D-Bus paths */
#define BLUEZ_SERVICE "org.bluez"
#define GATT_MANAGER_IFACE "org.bluez.GattManager1"
#define LE_ADVERTISING_MANAGER_IFACE "org.bluez.LEAdvertisingManager1"
#define GATT_SERVICE_IFACE "org.bluez.GattService1"
#define GATT_CHARACTERISTIC_IFACE "org.bluez.GattCharacteristic1"
#define DBUS_OM_IFACE "org.freedesktop.DBus.ObjectManager"
#define DBUS_PROP_IFACE "org.freedesktop.DBus.Properties"

#define APP_PATH "/com/example/smartglass"
#define SERVICE_PATH APP_PATH"/service0"
#define CHAR_PATH SERVICE_PATH"/char0"

static GDBusConnection *conn = NULL;
static GMainLoop *main_loop = NULL;
static guint service_id = 0;
static guint char_id = 0;

/* Characteristic value storage */
static GByteArray *char_value = NULL;

/* Logging function */
static void log_info(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[INFO] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

/* Write request handler - VULNERABLE CODE */
static void handle_write_request(const guint8 *data, gsize len) {
    char *decoded_text = g_strndup((const char*)data, len);
    
    log_info("通知を受信しました: %s", decoded_text);
    
    /* =================================================================
     * 【ここが脆弱性！】
     * 受信したテキストをサニタイズせず、そのままOSコマンドに埋め込んでいる。
     * 開発者の意図: echoコマンドを使ってログや画面に表示したいだけ。
     * ================================================================= */
    
    char command[1024];
    snprintf(command, sizeof(command), "echo \"Notification: %s\"", decoded_text);
    
    log_info("[SYSTEM] 実行するコマンド: %s", command);
    
    /* OSコマンドの実行 (ここで攻撃コードが走る) */
    system(command);
    
    g_free(decoded_text);
}

/* Method call handler for Characteristic */
static void handle_char_method_call(GDBusConnection *connection,
                                     const gchar *sender,
                                     const gchar *object_path,
                                     const gchar *interface_name,
                                     const gchar *method_name,
                                     GVariant *parameters,
                                     GDBusMethodInvocation *invocation,
                                     gpointer user_data) {
    if (g_strcmp0(method_name, "WriteValue") == 0) {
        GVariant *value_variant;
        GVariantIter *options;
        
        g_variant_get(parameters, "(@ay@a{sv})", &value_variant, &options);
        
        gsize len;
        gconstpointer data = g_variant_get_fixed_array(value_variant, &len, sizeof(guint8));
        
        /* Update stored value */
        if (char_value) {
            g_byte_array_free(char_value, TRUE);
        }
        char_value = g_byte_array_sized_new(len);
        g_byte_array_append(char_value, data, len);
        
        /* Handle the write request */
        handle_write_request((const guint8*)data, len);
        
        g_variant_unref(value_variant);
        g_variant_iter_free(options);
        
        g_dbus_method_invocation_return_value(invocation, NULL);
    } else if (g_strcmp0(method_name, "ReadValue") == 0) {
        GVariantBuilder *builder = g_variant_builder_new(G_VARIANT_TYPE("ay"));
        if (char_value) {
            for (guint i = 0; i < char_value->len; i++) {
                g_variant_builder_add(builder, "y", char_value->data[i]);
            }
        }
        GVariant *value = g_variant_new("(ay)", builder);
        g_variant_builder_unref(builder);
        g_dbus_method_invocation_return_value(invocation, value);
    }
}

/* Property getter for Characteristic */
static GVariant* handle_char_get_property(GDBusConnection *connection,
                                           const gchar *sender,
                                           const gchar *object_path,
                                           const gchar *interface_name,
                                           const gchar *property_name,
                                           GError **error,
                                           gpointer user_data) {
    if (g_strcmp0(property_name, "UUID") == 0) {
        return g_variant_new_string(CHAR_UUID);
    } else if (g_strcmp0(property_name, "Service") == 0) {
        return g_variant_new_object_path(SERVICE_PATH);
    } else if (g_strcmp0(property_name, "Flags") == 0) {
        GVariantBuilder *builder = g_variant_builder_new(G_VARIANT_TYPE("as"));
        g_variant_builder_add(builder, "s", "write");
        g_variant_builder_add(builder, "s", "write-without-response");
        return g_variant_new("as", builder);
    } else if (g_strcmp0(property_name, "Value") == 0) {
        GVariantBuilder *builder = g_variant_builder_new(G_VARIANT_TYPE("ay"));
        if (char_value) {
            for (guint i = 0; i < char_value->len; i++) {
                g_variant_builder_add(builder, "y", char_value->data[i]);
            }
        }
        return g_variant_new("ay", builder);
    }
    return NULL;
}

/* Property getter for Service */
static GVariant* handle_service_get_property(GDBusConnection *connection,
                                              const gchar *sender,
                                              const gchar *object_path,
                                              const gchar *interface_name,
                                              const gchar *property_name,
                                              GError **error,
                                              gpointer user_data) {
    if (g_strcmp0(property_name, "UUID") == 0) {
        return g_variant_new_string(SERVICE_UUID);
    } else if (g_strcmp0(property_name, "Primary") == 0) {
        return g_variant_new_boolean(TRUE);
    } else if (g_strcmp0(property_name, "Characteristics") == 0) {
        GVariantBuilder *builder = g_variant_builder_new(G_VARIANT_TYPE("ao"));
        g_variant_builder_add(builder, "o", CHAR_PATH);
        return g_variant_new("ao", builder);
    }
    return NULL;
}

/* Register GATT service and characteristic */
static gboolean register_gatt_service(void) {
    GError *error = NULL;
    
    /* Characteristic interface */
    GDBusInterfaceVTable char_vtable = {
        .method_call = handle_char_method_call,
        .get_property = handle_char_get_property,
        .set_property = NULL
    };
    
    static const gchar char_introspection[] =
        "<node>"
        "  <interface name='org.bluez.GattCharacteristic1'>"
        "    <method name='ReadValue'>"
        "      <arg type='a{sv}' name='options' direction='in'/>"
        "      <arg type='ay' name='value' direction='out'/>"
        "    </method>"
        "    <method name='WriteValue'>"
        "      <arg type='ay' name='value' direction='in'/>"
        "      <arg type='a{sv}' name='options' direction='in'/>"
        "    </method>"
        "    <property type='s' name='UUID' access='read'/>"
        "    <property type='o' name='Service' access='read'/>"
        "    <property type='ay' name='Value' access='read'/>"
        "    <property type='as' name='Flags' access='read'/>"
        "  </interface>"
        "</node>";
    
    GDBusNodeInfo *char_info = g_dbus_node_info_new_for_xml(char_introspection, &error);
    if (!char_info) {
        g_printerr("Error parsing char XML: %s\n", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    char_id = g_dbus_connection_register_object(conn, CHAR_PATH,
                                                 char_info->interfaces[0],
                                                 &char_vtable, NULL, NULL, &error);
    g_dbus_node_info_unref(char_info);
    
    if (!char_id) {
        g_printerr("Error registering characteristic: %s\n", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    /* Service interface */
    GDBusInterfaceVTable service_vtable = {
        .method_call = NULL,
        .get_property = handle_service_get_property,
        .set_property = NULL
    };
    
    static const gchar service_introspection[] =
        "<node>"
        "  <interface name='org.bluez.GattService1'>"
        "    <property type='s' name='UUID' access='read'/>"
        "    <property type='b' name='Primary' access='read'/>"
        "    <property type='ao' name='Characteristics' access='read'/>"
        "  </interface>"
        "</node>";
    
    GDBusNodeInfo *service_info = g_dbus_node_info_new_for_xml(service_introspection, &error);
    if (!service_info) {
        g_printerr("Error parsing service XML: %s\n", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    service_id = g_dbus_connection_register_object(conn, SERVICE_PATH,
                                                    service_info->interfaces[0],
                                                    &service_vtable, NULL, NULL, &error);
    g_dbus_node_info_unref(service_info);
    
    if (!service_id) {
        g_printerr("Error registering service: %s\n", error->message);
        g_error_free(error);
        return FALSE;
    }
    
    log_info("GATT サービスとキャラクタリスティックを登録しました");
    return TRUE;
}

int main(int argc, char *argv[]) {
    GError *error = NULL;
    
    log_info("スマートグラス(Bluetooth Server)を起動します...");
    
    /* Initialize */
    char_value = g_byte_array_new();
    
    /* Connect to system bus */
    conn = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &error);
    if (!conn) {
        g_printerr("Failed to connect to D-Bus: %s\n", error->message);
        g_error_free(error);
        return 1;
    }
    
    /* Register GATT service */
    if (!register_gatt_service()) {
        g_printerr("Failed to register GATT service\n");
        return 1;
    }
    
    log_info("SmartGlass_Demo として起動しました");
    log_info("スマホからの接続を待機中...");
    
    /* Run main loop */
    main_loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(main_loop);
    
    /* Cleanup */
    if (char_id)
        g_dbus_connection_unregister_object(conn, char_id);
    if (service_id)
        g_dbus_connection_unregister_object(conn, service_id);
    if (char_value)
        g_byte_array_free(char_value, TRUE);
    if (conn)
        g_object_unref(conn);
    if (main_loop)
        g_main_loop_unref(main_loop);
    
    return 0;
}