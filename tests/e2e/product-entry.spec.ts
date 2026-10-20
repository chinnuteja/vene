import {test,expect} from '@playwright/test';
import {evidence} from './platform';

test('entry explains the complete product and opens an ordinary workspace invitation',async({page})=>{
  await page.goto('/demo');
  const scope=page.getByRole('region',{name:'Full product capabilities'});
  await expect(scope).toContainText('Labs, imaging, specialist intake and prescription pickup');
  await expect(scope).toContainText('Prior-authorization submissions');
  await expect(scope).toContainText('Fictional offices and health-plan responses');
  await page.screenshot({path:evidence('product-entry-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:evidence('product-entry-mobile.png'),fullPage:true});
  await scope.getByRole('link',{name:'Open complete workspace'}).click();
  await page.getByLabel('Fictional encounter',{exact:true}).selectOption('james');
  await page.getByRole('button',{name:/^Continue as James\b/}).click();
  await expect(page).toHaveURL(/\/prepare$/);
  await expect(page.getByText('Follow-up with Dr. Chen',{exact:true})).toBeVisible();
  await page.goto('/dev');
  await page.getByLabel('Fictional encounter',{exact:true}).selectOption('james');
  await page.getByRole('button',{name:/^Continue as Nina\b/}).click();
  await expect(page.getByRole('button',{name:'Suggest to James',exact:true})).toBeVisible();
  await expect(page.getByText('Maria will decide whether to bring it.',{exact:false})).toHaveCount(0);
});
