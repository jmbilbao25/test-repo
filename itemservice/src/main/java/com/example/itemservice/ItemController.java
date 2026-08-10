package com.example.itemservice;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/items")
public class ItemController {

    private static final String[] CATEGORIES = {"Tools", "Books", "Food", "Toys", "Parts"};

    // Builds the list on every request. This is on purpose so there is
    // something to actually watch in VisualVM.
    @GetMapping
    public List<Item> getItems(@RequestParam(defaultValue = "5000") int count) {
        List<Item> items = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            String name = "Item " + i + " - " + CATEGORIES[i % CATEGORIES.length];
            items.add(new Item(i, name, CATEGORIES[i % CATEGORIES.length], 10.0 + (i % 100)));
        }
        return items;
    }
}
