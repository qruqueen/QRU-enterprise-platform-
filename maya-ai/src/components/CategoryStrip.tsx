import { CATEGORIES, type CategoryId } from "../types";

interface CategoryStripProps {
  activeCategories: CategoryId[];
}

export default function CategoryStrip({ activeCategories }: CategoryStripProps) {
  return (
    <ul className="category-strip" aria-label="Money categories this scenario touches">
      {CATEGORIES.map((category) => {
        const active = activeCategories.includes(category.id);
        return (
          <li
            key={category.id}
            className={`category-chip${active ? " category-chip--active" : ""}`}
            aria-current={active ? "true" : undefined}
            title={category.covers}
          >
            <span className="category-chip-emoji" aria-hidden="true">
              {category.emoji}
            </span>
            <span className="category-chip-name">{category.name}</span>
          </li>
        );
      })}
    </ul>
  );
}
