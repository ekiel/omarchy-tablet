/* Optional live-test helper using wlr-virtual-pointer-unstable-v1.
 * Build instructions and the upstream protocol URL are in docs/validation.md.
 * Coordinates are logical screen coordinates, supplied with their extents.
 * Usage: pointer x y width height [hold_ms | end_x end_y]
 */
#include <wayland-client.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "tablet-pointer.h"

static struct zwlr_virtual_pointer_manager_v1 *manager;

static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version) {
    (void)data;
    (void)version;
    if (!strcmp(interface, "zwlr_virtual_pointer_manager_v1"))
        manager = wl_registry_bind(registry, name,
                                   &zwlr_virtual_pointer_manager_v1_interface, 1);
}

static void removed(void *data, struct wl_registry *registry, uint32_t name) {
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener listener = {global, removed};

static uint32_t now(void) {
    struct timespec time;
    clock_gettime(CLOCK_MONOTONIC, &time);
    return time.tv_sec * 1000 + time.tv_nsec / 1000000;
}

static void frame(struct wl_display *display, struct zwlr_virtual_pointer_v1 *pointer) {
    zwlr_virtual_pointer_v1_frame(pointer);
    wl_display_roundtrip(display);
}

int main(int argc, char **argv) {
    if (argc < 5 || argc > 7)
        return 2;
    int x = atoi(argv[1]), y = atoi(argv[2]);
    int width = atoi(argv[3]), height = atoi(argv[4]);
    if (width <= 0 || height <= 0 || x < 0 || y < 0)
        return 2;
    struct wl_display *display = wl_display_connect(NULL);
    if (!display)
        return 3;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL);
    wl_display_roundtrip(display);
    if (!manager)
        return 4;
    struct zwlr_virtual_pointer_v1 *pointer =
        zwlr_virtual_pointer_manager_v1_create_virtual_pointer(manager, NULL);
    zwlr_virtual_pointer_v1_motion_absolute(pointer, now(), x, y, width, height);
    frame(display, pointer);
    usleep(100000);
    zwlr_virtual_pointer_v1_button(pointer, now(), 272, WL_POINTER_BUTTON_STATE_PRESSED);
    frame(display, pointer);
    if (argc == 7) {
        int end_x = atoi(argv[5]), end_y = atoi(argv[6]);
        for (int step = 1; step <= 15; step++) {
            usleep(20000);
            zwlr_virtual_pointer_v1_motion_absolute(pointer, now(),
                x + (end_x - x) * step / 15, y + (end_y - y) * step / 15, width, height);
            frame(display, pointer);
        }
    } else {
        usleep(argc == 6 ? (unsigned)atoi(argv[5]) * 1000 : 80000);
    }
    zwlr_virtual_pointer_v1_button(pointer, now(), 272, WL_POINTER_BUTTON_STATE_RELEASED);
    frame(display, pointer);
    usleep(100000);
    zwlr_virtual_pointer_v1_destroy(pointer);
    zwlr_virtual_pointer_manager_v1_destroy(manager);
    wl_registry_destroy(registry);
    wl_display_flush(display);
    wl_display_disconnect(display);
    return 0;
}
